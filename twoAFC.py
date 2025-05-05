import random

import numpy as np
import pandas as pd
from lecilab_behavior_analysis.utils import (get_block_size_uniform_pm30,
                                             get_right_bias, get_sound_stats)
from village.classes.task import Event, Output, Task

from sound_functions import cloud_of_tones_matrices, sound_matrix_to_sound, speaker_dict


class TwoAFC(Task):
    def __init__(self):
        super().__init__()

        self.info = """

        Two Alternative Force Choice Task
        -------------------

        It works with visual and auditory modality, or both.
        It has an anti-bias. #TODO: make sure it works as expected
        Implement opto. #TODO
        
        The progression through the stages is defined in the training_settings.py file.

           (\(\  
          ( -.-)
        o_(")(")        ʕ·ᴥ·ʔ

             @..@
            (----)
           ( >__< )
           ^^    ^^

        """

        # variables are defined in training_settings.py

    def start(self):

        print("TwoAFC starts in stage {0}".format(self.settings.current_training_stage))

        ## Initiate conditions that won't change during training
        # Time the valve needs to open to deliver the reward amount
        # Make sure to calibrate the valve/pump before using it, otherwise
        # you will get errors
        self.left_valve_opening_time = self.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_amount_ml
        )
        self.right_valve_opening_time = self.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_amount_ml
        )

        # determine if punishment will be used
        if self.settings.punishment:
            self.punish_condition = "punish_state"
        else:
            # if no punishment is used, let the mouse choose again
            self.punish_condition = "stimulus_state"

        # determine the initial holding time for the center port
        # Total holding time
        self.time_to_hold_response = self.settings.holding_response_time
        # Remaining holding time
        self.remaining_holding_time = self.time_to_hold_response - self.settings.holding_response_time_min
        # If it is 0 or negative, set it to something small
        if self.remaining_holding_time <= 0:
            self.remaining_holding_time = 0.001

        # if doing multisensory, set the modality to random and generate a block
        if self.settings.stimulus_modality == "multisensory":
            self.stimulus_modality = random.choice(["visual", "auditory"])
            self.current_stim_mod_block_trials_left = get_block_size_uniform_pm30(
                self.settings.stimulus_modality_block_size
            )
            self.stim_mod_block_counter = 1
        # if doing auditory or multisensory, set the contingency
        if self.settings.stimulus_modality in ["auditory", "multisensory"]:
            match self.settings.frequency_associated_with_left_choice:
                case "low":
                    self.auditory_contingency = {"left": "low", "right": "high"}
                case "high":
                    self.auditory_contingency = {"left": "high", "right": "low"}
                case _:
                    raise ValueError("Frequency associated with left choice not recognized")

        # if anti-bias is on, set the information of the last X trials
        if self.settings.anti_bias_on:
            # first
            self.last_trials_vector = {
                "side": np.full(int(self.settings.anti_bias_vector_size), "ignore"), # ignore the first trials
                "correct": np.full(int(self.settings.anti_bias_vector_size), False),
            }

        # initialize the variables that will hold the stimuli for the trial
        self.trial_visual_stimulus = None
        self.trial_auditory_stimulus = None

        # initialize the sound properties
        self.get_sound_from_settings()
        # create a variable in manager to store the sound
        self.twoAFC_sound = None
        # find the speaker that this system is using
        self.speaker = speaker_dict(self.settings.speaker_name)

        # create the dictionary for the difficulty of trials and the stimulus properties
        self.trial_difficulty_parameters = {}
        if self.settings.easy_trials_on:
            self.trial_difficulty_parameters["easy"] = {
                    "light_intensity_difference": self.settings.easy_light_intensity_difference,
                    "frequency_proportion": self.settings.easy_frequency_proportion,
                }
        if self.settings.medium_trials_on:
            self.trial_difficulty_parameters["medium"] = {
                    "light_intensity_difference": self.settings.medium_light_intensity_difference,
                    "frequency_proportion": self.settings.medium_frequency_proportion,
                }
        if self.settings.hard_trials_on:
            self.trial_difficulty_parameters["hard"] = {
                    "light_intensity_difference": self.settings.hard_light_intensity_difference,
                    "frequency_proportion": self.settings.hard_frequency_proportion,
                }

    def create_trial(self):
        """
        This function updates the variables that will be used every trial
        """
        print("Creating trial {0}".format(str(self.current_trial)))

        ## Start the task
        # Trial start state: Turn on light in the middle port
        # Things can be appended elsewhere to this state like loading the sound
        self.ready_to_initiate_output = [
            (
                Output.PWM2,
                int(self.settings.middle_port_light_intensity * 255),
            ),
            # stop the sound if it is playing
            Output.SoftCode1,
        ]

        # define the modality of the stimulus
        self.set_stimulus_modality()
        # pick a trial type. For now, random
        self.generate_trial_type()
        ## Set the variables for the stimulus states and the possible choices
        self.set_stimulus_state_conditions()
        # assemble the state machine
        self.assemble_state_machine()

    def assemble_state_machine(self) -> None:
        # 'start_of_trial' state that sends a TTL pulse from the BNC channel 2
        # This can be used to synchronize the task with other devices (not used here)
        self.bpod.add_state(
            state_name="start_of_trial",
            state_timer=0.001,
            state_change_conditions={Event.Tup: "ready_to_initiate"},
            output_actions=[Output.BNC2High],
        )

        # 'ready_to_initiate' state that waits for the poke in the middle port
        self.bpod.add_state(
            state_name="ready_to_initiate",
            state_timer=0,
            state_change_conditions={Event.Port2In: "hold_center_port"},
            output_actions=self.ready_to_initiate_output,
        )

        # 'hold_center_port' state that waits for the mouse to hold the center port
        # the minimum time is defined in the settings
        self.bpod.add_state(
            state_name="hold_center_port",
            state_timer=self.settings.time_to_hold_response_min,
            state_change_conditions={
                Event.Port2Out: "ready_to_initiate",
                Event.Tup: "hold_while_stimulus",
            },
            output_actions=[],
        )
        # TODO: implement another punishment if early time out
        self.bpod.add_state(
            state_name="hold_while_stimulus",
            state_timer=self.remaining_holding_time,
            state_change_conditions={
                Event.Port2Out: "ready_to_initiate",
                Event.Tup: "stimulus_state"
            },
            output_actions=self.hold_while_stimulus_state_output,
        )

        self.bpod.add_state(
            state_name="stimulus_state",
            state_timer=self.settings.timer_for_response,
            state_change_conditions={
                Event.Port1In: self.left_poke_action,
                Event.Port3In: self.right_poke_action,
                Event.Tup: "exit",
            },
            output_actions=self.stimulus_state_output,
        )

        self.bpod.add_state(
            state_name="reward_state",
            state_timer=self.valve_opening_time,
            state_change_conditions={Event.Tup: "iti"},
            output_actions=[self.valve_to_open],
        )

        self.bpod.add_state(
            state_name="punish_state",
            state_timer=self.settings.punishment_time,
            state_change_conditions={Event.Tup: "iti"},
            output_actions=[],
        )

        # iti is the time that the mouse has to wait before the next trial
        self.bpod.add_state(
            state_name="iti",
            state_timer=self.settings.iti,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[],
        )

    def after_trial(self) -> None:
        # register the training stage
        self.register_value("current_training_stage", self.settings.current_training_stage)
        # we will also record the trial type, which will be used by training_settings.py
        # to make sure that the animal does not go from the second stage to the first one
        self.register_value("correct_side", self.this_trial_side)
        # register the modality of the stimulus
        self.register_value("stimulus_modality", self.stimulus_modality)
        # register the difficulty of the trial
        self.register_value("difficulty", self.this_trial_difficulty)
        # register the actual stimuli used
        self.register_value("visual_stimulus", self.trial_visual_stimulus)
        self.register_value("auditory_stimulus", self.trial_auditory_stimulus)
        # register the actual auditory statistics
        if self.trial_auditory_stimulus is not None:
            sound_stats = get_sound_stats(self.trial_auditory_stimulus)
            self.register_value("auditory_real_statistics", sound_stats)
            # reset the sound in the manager
            self.twoAFC_sound = None
        # reset them to None for the next trial
        self.trial_visual_stimulus = None
        self.trial_auditory_stimulus = None
        # if multisensory, register the block number
        if self.settings.stimulus_modality == "multisensory":
            self.register_value(
                "stimulus_modality_block_number", self.stim_mod_block_counter
            )
        # we will also record if the trial was correct or not
        was_trial_correct = self.get_performance_of_trial()
        self.register_value("correct", was_trial_correct)

        # register the amount of water given to the mouse in this trial
        # do not delete this variable, it is used to calculate the water consumption
        # and trigger alarms. You can override the alarms in the GUI
        if self.has_state_occurred("STATE_reward_state_START"):
            self.register_value("water", self.settings.reward_amount_ml)
        else:
            self.register_value("water", 0)

        # print information to screen
        print("\t{0} {1} trial was {2}".format(
            self.this_trial_side,
            self.this_trial_difficulty,
            "correct" if was_trial_correct else "incorrect"
            )
        )

        # store the holding time
        self.register_value("holding_time", self.time_to_hold_response)
        # if trial was correct, increase the holding time with a limit
        if was_trial_correct:
            new_holding_time = (
                self.time_to_hold_response + self.settings.holding_response_time_step
            )
            self.time_to_hold_response = min(
                new_holding_time, self.settings.holding_response_time_max
            )
            new_remaining_holding_time = (
                self.time_to_hold_response - self.settings.holding_response_time_min
            )
            self.remaining_holding_time = max(
                new_remaining_holding_time, 0.001
            )

        # update the list of the last 15 trials for the anti-bias
        if self.settings.anti_bias_on:
            # shift each list one position to the right
            for key in self.last_trials_vector.keys():
                self.last_trials_vector[key] = np.roll(self.last_trials_vector[key], 1)
            self.last_trials_vector["side"][0] = self.this_trial_side
            self.last_trials_vector["correct"][0] = was_trial_correct

    def close(self) -> None:
        print("Closing the task")

    def generate_trial_type(self) -> None:
        # random side by default
        p = [0.5, 0.5]
        # change it if anti-bias is on
        # first 15 trials are ignored by the function that calculates the bias
        if self.settings.anti_bias_on:
            # find the bias of the mouse
            right_bias = get_right_bias(self.last_trials_vector)
            left_probability = (right_bias + 1) / 2
            right_probability = 1 - left_probability
            p = [left_probability, right_probability]

        self.this_trial_side = np.random.choice(self.settings.trial_sides, p=p)

        # random difficulty by default
        self.this_trial_difficulty = random.choice(list(self.trial_difficulty_parameters.keys()))

    def set_stimulus_modality(self) -> None:
        match self.settings.stimulus_modality:
            case "visual":
                self.stimulus_modality = "visual"
            case "auditory":
                self.stimulus_modality = "auditory"
            case "multisensory":
                self.current_stim_mod_block_trials_left -= 1
                if self.current_stim_mod_block_trials_left == 0:
                    # change the modality
                    if self.stimulus_modality == "visual":
                        self.stimulus_modality = "auditory"
                    else:
                        self.stimulus_modality = "visual"
                    # generate a new block
                    self.current_stim_mod_block_trials_left = (
                        get_block_size_uniform_pm30(self.settings.stimulus_modality_block_size)
                    )
                    self.stim_mod_block_counter += 1
                    print(
                        "Entering block {0}, with {1} amount of trials".format(
                            self.stim_mod_block_counter,
                            self.current_stim_mod_block_trials_left,
                        )
                    )
            case _:
                raise ValueError("Stimulus modality not recognized")

    def set_stimulus_state_conditions(self) -> None:
        # set the output for the stimulus state depending on the side
        if self.this_trial_side == "left":
            self.correct_port_ID = Output.PWM1
            self.incorrect_port_ID = Output.PWM3
            self.left_poke_action = "reward_state"
            self.right_poke_action = self.punish_condition
            self.valve_to_open = Output.Valve1
            self.valve_opening_time = self.left_valve_opening_time

        elif self.this_trial_side == "right":
            self.correct_port_ID = Output.PWM3
            self.incorrect_port_ID = Output.PWM1
            self.left_poke_action = self.punish_condition
            self.right_poke_action = "reward_state"
            self.valve_to_open = Output.Valve3
            self.valve_opening_time = self.right_valve_opening_time

        # define conditions based on the trial type
        match self.stimulus_modality:
            case "visual":
                # choose the incorrect brightness at random
                l_b, h_b = self.settings.side_port_wrong_intensities_extremes
                self.incorrect_brightness = random.uniform(l_b, h_b)
                # pick the correct brightness difference according to the difficulty
                self.correct_brightness = self.incorrect_brightness * (
                    self.trial_difficulty_parameters[
                        self.this_trial_difficulty
                    ]["light_intensity_difference"]
                )
                # store as the trial stimuli
                self.trial_visual_stimulus = (
                    self.correct_brightness,
                    self.incorrect_brightness,
                )
                # set the output of the stimulus states
                self.hold_while_stimulus_state_output = [
                    (
                        self.correct_port_ID,
                        int(self.correct_brightness * 255),
                    ),
                    (
                        self.incorrect_port_ID,
                        int(self.incorrect_brightness * 255),
                    ),
                ]
                self.stimulus_state_output = self.hold_while_stimulus_state_output
            case "auditory":
                # dominant frequency "low" or "high"
                dominant_freq = self.auditory_contingency[self.this_trial_side]
                # get the proportion of tones for the dominant frequency
                dominant_proportion = self.trial_difficulty_parameters[
                    self.this_trial_difficulty
                ]["frequency_proportion"] * 0.01
                # determine the proportion of high and low frequencies
                match dominant_freq:
                    case "low":
                        low_perc = dominant_proportion
                        high_perc = 1 - dominant_proportion
                    case "high":
                        low_perc = 1 - dominant_proportion
                        high_perc = dominant_proportion
                # randomize the amplitude of the high and low frequencies
                high_amplitude_mean = random.uniform(
                    self.settings.bottom_amplitude_mean,
                    self.settings.top_amplitude_mean,
                )
                # low_amplitude_mean = random.uniform(
                #     self.settings.bottom_amplitude_mean,
                #     self.settings.top_amplitude_mean,
                # )
                # same as high to not confuse the mouse
                low_amplitude_mean = high_amplitude_mean
                # create the sound structure
                high_mat, low_mat = cloud_of_tones_matrices(
                    **self.sound_properties,
                    high_prob=high_perc,
                    low_prob=low_perc,
                    high_amplitude_mean=high_amplitude_mean,
                    low_amplitude_mean=low_amplitude_mean,
                )
                # store the trial stimuli
                self.trial_auditory_stimulus = {
                    "high_tones": high_mat.to_dict(),
                    "low_tones": low_mat.to_dict(),
                }
                # calibrate the sound applying self.get_sound_gain to all values of the matrices
                high_mat_calibrated = high_mat.applymap(
                    lambda db: self.get_sound_gain(
                        self.speaker,
                        db,
                        "high_tones_calibration_matrix",
                        )
                )
                low_mat_calibrated = low_mat.applymap(
                    lambda db: self.get_sound_gain(
                        self.speaker,
                        db,
                        "low_tones_calibration_matrix",
                        )
                )
                # generate the sound
                sound = sound_matrix_to_sound(
                    pd.concat([high_mat_calibrated, low_mat_calibrated], axis=1),
                    **self.sound_properties,
                )

                # add the sound to manager so it is accessible by the softcode functions
                self.twoAFC_sound = sound
                # load the sound to the Bpod in the ready_to_initiate state
                self.ready_to_initiate_output.append(Output.SoftCode2)
                # play the sound on the stimulus state
                self.hold_while_stimulus_state_output = [Output.SoftCode3]
                # the sound plays if not stopped
                self.stimulus_state_output = []

    
    def get_sound_from_settings(self) -> None:
        list_of_frequencies = np.logspace(
            np.log10(self.settings.lowest_frequency),
            np.log10(self.settings.highest_frequency),
            int(self.settings.number_of_frequencies * 3),
        ).round(0).tolist()
        low_freq_list = list_of_frequencies[: int(self.settings.number_of_frequencies)]
        high_freq_list = list_of_frequencies[-int(self.settings.number_of_frequencies) :]
        self.sound_properties = {
            "sample_rate": self.settings.sample_rate,
            "duration": self.settings.sound_duration,
            "high_freq_list": high_freq_list,
            "low_freq_list": low_freq_list,
            "amplitude_std": self.settings.amplitude_std,
            "subduration": self.settings.tone_duration,
            "suboverlap": self.settings.tone_overlap,
            "ramp_time": self.settings.tone_ramp_time,
        }
    
    def get_performance_of_trial(self) -> bool:
        """
        This method calculates the performance of a trial, comparing the trial type
        to the first port that the mouse poked.
        You can access the trial information in self.trial_data
        """
        # get the side port that the mouse poked first
        first_poke = self.first_poke_after_stimulus_state()
        # check if the mouse poked the correct port
        if first_poke == "Port1In" and self.this_trial_side == "left":
            return True
        elif first_poke == "Port3In" and self.this_trial_side == "right":
            return True
        else:
            return False

    def first_poke_after_stimulus_state(self):
        stim_state_array = self.trial_data["STATE_stimulus_state_START"]
        if len(stim_state_array) == 0:
            return None
        start_time = max(stim_state_array)
        # check if the keys are in the dict
        if "Port1In" in self.trial_data.keys():
            port1_in = self.trial_data["Port1In"]
            if type(port1_in) is float:
                port1_in = [port1_in]
        else:
            port1_in = []
        if "Port3In" in self.trial_data.keys():
            port3_in = self.trial_data["Port3In"]
            if type(port3_in) is float:
                port3_in = [port3_in]
        else:
            port3_in = []       
        
        port1_in_after = [i for i in port1_in if i > start_time]
        port3_in_after = [i for i in port3_in if i > start_time]
        
        if len(port1_in_after) == 0 and len(port3_in_after) == 0:
            return None
        elif len(port1_in_after) == 0:
            return "Port3In"
        elif len(port3_in_after) == 0:
            return "Port1In"
        
        if np.min(port1_in_after) < np.min(port3_in_after):
            return "Port1In"
        elif np.min(port3_in_after) < np.min(port1_in_after):
            return "Port3In"
        else:
            return None
    
    def has_state_occurred(self, state_name: str) -> bool:
        """
        This method checks if a state has occurred in the trial
        """
        if state_name not in self.trial_data.keys():
            return False
        elif len(self.trial_data[state_name]) == 0:
            return False
        # if all is nan
        elif all(np.isnan(self.trial_data[state_name])):
            return False
        else:
            return True


# Uncomment below if you want to programatically interact with
# with your task and bpod. This is useful for debugging and for
# testing the task.

# if __name__ == "__main__":
#     import time

#     from training_settings import TrainingSettings

#     task = TwoAFC()
#     training = TrainingSettings()
#     training.default_training_settings()
#     task.settings = training.settings

#     task.run_in_thread()
#     time.sleep(2)
#     # poke in the middle port
#     task.bpod.manual_override_input("Port2In")
#     time.sleep(0.3)
#     task.bpod.manual_override_input("Port2Out")
#     # poke in the left port
#     task.bpod.manual_override_input("Port1In")
#     task.bpod.manual_override_input("Port1Out")
#     time.sleep(0.2)
#     # poke in the right port
#     task.bpod.manual_override_input("Port3In")
#     task.bpod.manual_override_input("Port3Out")
#     # leave enough time for the bpod to finish
#     time.sleep(2)

#     time.sleep(2)
