# TODO (analysis code): the "visual_stimulus" column changed meaning.
#   Before (main, new_tv, nuo_dev): (brightness of correct port, brightness of incorrect port)
#   Now (hmv_claude, from 2026-11-09): (brightness of LEFT port, brightness of RIGHT port)
#   Modality names also changed ("auditory" -> "auditory-cot", ...), and "correct"
#   can be None (timeouts).
#   lecilab_behavior_analysis reads both versions from its branch hmv_claude:
#   see lecilab_behavior_analysis/data_format_changes.py, which documents each
#   change and the date it applies from.
#   Remove this TODO once that branch is merged and installed on the rigs.

import random

import numpy as np
import pandas as pd
from lecilab_behavior_analysis.utils import (get_block_size_uniform_pm30,
                                             get_right_bias, get_sound_stats)
from village.custom_classes.task_base import (
    BpodEvent as Event,
    BpodOutput as Output,
    TaskBase,
)

from sound_functions import cloud_of_tones_matrices, sound_matrix_to_sound, speaker_dict, white_noise
# only functions and constants are imported (not the TrainingProtocol class),
# so that village does not find the training protocol in this module too
from training_protocol import (
    ALL_MODALITIES,
    MULTISENSORY,
    SINGLE_MODALITIES,
    get_block_modalities,
    get_training_sequence,
    parse_stage,
)


class TwoAFC(TaskBase):
    def __init__(self):
        super().__init__()

        self.info = r"""

        Two Alternative Force Choice Task
        -------------------

        Modalities (the cue that tells where the reward is):
        - visual: the brighter side port
        - auditory-cot: cloud of tones, dominant frequency
        - auditory-local-wn: white noise from the side of the reward
        - multisensory: blocks alternating the single modalities
          of the training sequence
        Optional distractors (uninformative, only in trials of another modality):
        random light (random_visual_stimulus) and
        random cloud of tones in visual trials (random_COT_stimulus).
        It has an anti-bias.
        Implement opto. #TODO

        The progression through the stages is defined in the training_protocol.py file.

           (\(\  
          ( -.-)
        o_(")(")        ʕ·ᴥ·ʔ

             @..@
            (----)
           ( >__< )
           ^^    ^^

        """

        # variables are defined in training_protocol.py

    def start(self):

        print("TwoAFC starts in stage {0}".format(self.settings.current_training_stage))

        ## Initiate conditions that won't change during training
        # Time the valve needs to open to deliver the reward amount
        # Make sure to calibrate the valve/pump before using it, otherwise
        # you will get errors
        self.left_valve_opening_time = self.calibrations.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_amount_ul
        )
        self.right_valve_opening_time = self.calibrations.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_amount_ul
        )

        # determine if punishment will be used
        if self.settings.punishment:
            self.punish_condition = "punish_state"
        else:
            # if no punishment is used, let the mouse choose again
            self.punish_condition = "stimulus_state"
        
        # determine if poking out of the center port early will punish
        if self.settings.early_poke_punishment:
            self.early_poke_punish_condition = "punish_state"
        else:
            self.early_poke_punish_condition = "ready_to_initiate"

        # determine the initial holding time for the center port
        # Total holding time, always a number between the min and the max
        # (a NaN timer would make the Bpod state machine fail)
        holding_min = self.settings.holding_response_time_min
        holding_max = self.settings.holding_response_time_max
        try:
            holding_time = float(self.settings.holding_response_time)
        except (TypeError, ValueError):
            holding_time = np.nan
        if not np.isfinite(holding_time):
            print(
                "Warning: holding_response_time is {0}, using the minimum {1}".format(
                    self.settings.holding_response_time, holding_min
                )
            )
            holding_time = holding_min
        elif not holding_min <= holding_time <= holding_max:
            clipped = min(max(holding_time, holding_min), holding_max)
            print(
                "Warning: holding_response_time {0} is outside [{1}, {2}], "
                "using {3}".format(holding_time, holding_min, holding_max, clipped)
            )
            holding_time = clipped
        self.time_to_hold_response = holding_time
        # Remaining holding time
        self.remaining_holding_time = self.time_to_hold_response - self.settings.holding_response_time_min
        # If it is 0 or negative, set it to something small
        if self.remaining_holding_time <= 0:
            self.remaining_holding_time = 0.001

        # modality of the session: it comes from the stage name, except in
        # Manual_training, where it comes from the manual_training_modality setting
        if self.settings.current_training_stage == "Manual_training":
            self.session_modality = self.settings.manual_training_modality
        else:
            self.session_modality, _ = parse_stage(self.settings.current_training_stage)
        if self.session_modality not in ALL_MODALITIES:
            raise ValueError(
                "Stimulus modality {0} not recognized".format(self.session_modality)
            )

        # if doing multisensory, alternate in blocks the single modalities
        # of the training sequence, starting with a random one
        if self.session_modality == MULTISENSORY:
            self.block_modalities = get_block_modalities(
                get_training_sequence(self.settings)
            )
            if len(self.block_modalities) < 2:
                raise ValueError(
                    "Multisensory needs two single modalities in the training sequence"
                )
            self.stimulus_modality = random.choice(self.block_modalities)
            self.current_stim_mod_block_trials_left = get_block_size_uniform_pm30(
                self.settings.stimulus_modality_block_size
            )
            self.stim_mod_block_counter = 1
        # set the contingency of the cloud of tones (used when it is the cue).
        # Always checked, so that a wrong setting fails at the start of the session
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
        self.trial_auditory_output_side = None

        # initialize the sound properties
        self.get_sound_from_settings()
        # variable of the task that stores the sound of the trial
        # (the softcode functions read it from here)
        self.twoAFC_sound = None
        # find the speakers that this system is using
        speaker_config = speaker_dict[self.system_name]
        if isinstance(speaker_config, dict):
            self.speakers = speaker_config
        else:
            self.speakers = {"left": speaker_config, "right": speaker_config}

        # create the dictionary for the difficulty of trials and the stimulus properties
        self.trial_difficulty_parameters = {}
        if self.settings.easy_trials_on:
            self.trial_difficulty_parameters["easy"] = {
                "light_intensity_difference": self.settings.easy_light_intensity_difference,
                "location_db_range": self.settings.easy_location_db_range,
                "frequency_proportion": self.settings.easy_frequency_proportion,
            }

        if self.settings.medium_trials_on:
            self.trial_difficulty_parameters["medium"] = {
                "light_intensity_difference": self.settings.medium_light_intensity_difference,
                "location_db_range": self.settings.medium_location_db_range,
                "frequency_proportion": self.settings.medium_frequency_proportion,
            }

        if self.settings.hard_trials_on:
            self.trial_difficulty_parameters["hard"] = {
                "light_intensity_difference": self.settings.hard_light_intensity_difference,
                "location_db_range": self.settings.hard_location_db_range,
                "frequency_proportion": self.settings.hard_frequency_proportion,
            }

        if len(self.trial_difficulty_parameters) == 0:
            raise ValueError(
                "At least one of easy_trials_on, medium_trials_on or "
                "hard_trials_on must be True"
            )

        # if lights can be used in this session, the brighter port must not go
        # above the maximum brightness (1), or the Bpod state machine fails
        lights_used = (
            self.session_modality == "visual"
            or self.settings.random_visual_stimulus
            or (
                self.session_modality == MULTISENSORY
                and "visual" in self.block_modalities
            )
        )
        if lights_used:
            highest_dimmer_brightness = self.settings.side_port_wrong_intensities_extremes[1]
            largest_difference = max(
                parameters["light_intensity_difference"]
                for parameters in self.trial_difficulty_parameters.values()
            )
            if highest_dimmer_brightness * largest_difference > 1:
                raise ValueError(
                    "The brighter port could reach a brightness of {0:.3f} (maximum 1): "
                    "side_port_wrong_intensities_extremes[1] ({1}) x the largest active "
                    "light_intensity_difference ({2}). Lower one of them.".format(
                        highest_dimmer_brightness * largest_difference,
                        highest_dimmer_brightness,
                        largest_difference,
                    )
                )

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
        # keep the light on in the middle port while holding
        self.hold_center_port_output = [
            (
                Output.PWM2,
                int(self.settings.middle_port_light_intensity * 255),
            )
        ]
        self.hold_while_stimulus_state_output = [
            (
                Output.PWM2,
                int(self.settings.middle_port_light_intensity * 255),
            )
        ]
        # initialize stimulus state output, it will be updated in set_stimulus_state_conditions
        self.stimulus_state_output = []
        # define the output of the punish state
        self.punish_condition_output = [
            Output.SoftCode4,  # stop sound and play white noise
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
            state_timer=self.settings.holding_response_time_min,
            state_change_conditions={
                Event.Port2Out: self.early_poke_punish_condition,
                Event.Tup: "hold_while_stimulus",
            },
            output_actions=self.hold_center_port_output,
        )
        # TODO: implement another punishment if early time out
        self.bpod.add_state(
            state_name="hold_while_stimulus",
            state_timer=self.remaining_holding_time,
            state_change_conditions={
                Event.Port2Out: self.early_poke_punish_condition,
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
            output_actions=self.punish_condition_output,
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
        # register the reward side of the trial
        self.register_value("correct_side", self.this_trial_side)
        # register the modality of the stimulus
        self.register_value("stimulus_modality", self.stimulus_modality)
        # register the difficulty of the trial
        self.register_value("difficulty", self.this_trial_difficulty)
        # register the actual stimuli used
        # (left, right) brightness of the side ports. See the TODO at the top of the file
        self.register_value("visual_stimulus", self.trial_visual_stimulus)
        self.register_value("auditory_stimulus", self.trial_auditory_stimulus)
        self.register_value("auditory_output_side", self.trial_auditory_output_side)
        # register the actual auditory statistics
        if self.trial_auditory_stimulus is not None:
            # only the cloud of tones (cue or distractor) has tone statistics
            if "high_tones" in self.trial_auditory_stimulus:
                sound_stats = get_sound_stats(self.trial_auditory_stimulus)
                self.register_value("auditory_real_statistics", sound_stats)
            # reset the sound of the trial
            self.twoAFC_sound = None
        # reset them to None for the next trial
        self.trial_visual_stimulus = None
        self.trial_auditory_stimulus = None
        self.trial_auditory_output_side = None
        # if multisensory, register the block number
        if self.session_modality == MULTISENSORY:
            self.register_value(
                "stimulus_modality_block_number", self.stim_mod_block_counter
            )
        # we will also record if the trial was correct or not
        # (True, False, or None on timeouts. Early withdrawals are False)
        was_trial_correct = self.get_performance_of_trial()
        self.register_value("correct", was_trial_correct)

        # register the amount of water given to the mouse in this trial
        # do not delete this variable, it is used to calculate the water consumption
        # and trigger alarms. You can override the alarms in the GUI
        if self.has_state_occurred("STATE_reward_state_START"):
            self.register_value("water", self.settings.reward_amount_ul)
        else:
            self.register_value("water", 0)

        # print information to screen
        if was_trial_correct is None:
            outcome = "a timeout"
        elif not self.has_state_occurred("STATE_stimulus_state_START"):
            outcome = "an early withdrawal"
        elif was_trial_correct:
            outcome = "correct"
        else:
            outcome = "incorrect"
        print("\t{0} {1} trial was {2}".format(
            self.this_trial_side,
            self.this_trial_difficulty,
            outcome,
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

        # update the list of the last X trials for the anti-bias
        # (trials without a side choice, timeouts and early withdrawals,
        # say nothing about the bias, so they are skipped)
        made_a_choice = self.first_poke_after_stimulus_state() is not None
        if self.settings.anti_bias_on and made_a_choice:
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
        # the anti-bias is off (p = 0.5) until anti_bias_vector_size trials
        # with a side choice have been made in this session
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
        """
        Sets self.stimulus_modality, the single modality of this trial (the cue).
        In multisensory it alternates in blocks the single modalities
        of the training sequence.
        """
        if self.session_modality in SINGLE_MODALITIES:
            self.stimulus_modality = self.session_modality
            return

        # multisensory
        self.current_stim_mod_block_trials_left -= 1
        if self.current_stim_mod_block_trials_left == 0:
            # change to the next modality of the sequence
            current_index = self.block_modalities.index(self.stimulus_modality)
            next_index = (current_index + 1) % len(self.block_modalities)
            self.stimulus_modality = self.block_modalities[next_index]
            # generate a new block
            self.current_stim_mod_block_trials_left = get_block_size_uniform_pm30(
                self.settings.stimulus_modality_block_size
            )
            self.stim_mod_block_counter += 1
            print(
                "Entering block {0} ({1}), with {2} trials".format(
                    self.stim_mod_block_counter,
                    self.stimulus_modality,
                    self.current_stim_mod_block_trials_left,
                )
            )

    def set_stimulus_state_conditions(self) -> None:
        """
        Sets the ports and the stimuli of the trial.
        - The cue is the stimulus of the trial modality (self.stimulus_modality),
          always contingent on the reward side.
        - Distractors (random_visual_stimulus, random_COT_stimulus) add an
          uninformative stimulus of their type, only in trials whose cue is
          a different type. They never randomize the cue.
        """
        self.set_port_conditions()

        cue = self.stimulus_modality

        # visual: cue, or distractor in non-visual trials
        if cue == "visual":
            self.add_visual_stimulus(informative=True)
        elif self.settings.random_visual_stimulus:
            self.add_visual_stimulus(informative=False)

        # cloud of tones: cue, or distractor in visual trials only
        # (not in white noise trials, so that the two sounds are never mixed)
        if cue == "auditory-cot":
            self.add_cot_stimulus(informative=True)
        elif cue == "visual" and self.settings.random_COT_stimulus:
            self.add_cot_stimulus(informative=False)

        # white noise from the side of the reward
        if cue == "auditory-local-wn":
            self.add_local_wn_stimulus()

    def set_port_conditions(self) -> None:
        # set the ports, actions and valves depending on the side
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

    def add_visual_stimulus(self, informative: bool) -> None:
        """
        Lights up both side ports with different brightness.
        If informative, the brightest port is the correct one.
        If not, the brightest port is chosen at random.
        """
        # choose the dimmer brightness at random
        l_b, h_b = self.settings.side_port_wrong_intensities_extremes
        lower_brightness = random.uniform(l_b, h_b)
        # pick the brightness difference according to the difficulty
        higher_brightness = lower_brightness * (
            self.trial_difficulty_parameters[
                self.this_trial_difficulty
            ]["light_intensity_difference"]
        )
        if informative:
            self.brightness_of_correct_port = higher_brightness
            self.brightness_of_incorrect_port = lower_brightness
        else:
            self.brightness_of_correct_port, self.brightness_of_incorrect_port = (
                random.sample([higher_brightness, lower_brightness], 2)
            )
        # store as the trial stimuli: (left, right) brightness
        if self.this_trial_side == "left":
            self.trial_visual_stimulus = (
                self.brightness_of_correct_port,
                self.brightness_of_incorrect_port,
            )
        else:
            self.trial_visual_stimulus = (
                self.brightness_of_incorrect_port,
                self.brightness_of_correct_port,
            )
        # set the output of the stimulus states
        self.hold_while_stimulus_state_output.extend([
            (self.correct_port_ID, int(self.brightness_of_correct_port * 255)),
            (self.incorrect_port_ID, int(self.brightness_of_incorrect_port * 255))
        ])
        self.stimulus_state_output.extend([
            (self.correct_port_ID, int(self.brightness_of_correct_port * 255)),
            (self.incorrect_port_ID, int(self.brightness_of_incorrect_port * 255)),
        ])

    def add_cot_stimulus(self, informative: bool) -> None:
        """
        Plays a cloud of tones. If informative, the dominant frequency follows
        the contingency of the reward side. If not, it is chosen at random.
        """
        # dominant frequency "low" or "high"
        if informative:
            dominant_freq = self.auditory_contingency[self.this_trial_side]
        else:
            dominant_freq = random.choice(["low", "high"])
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
        # same as high to not confuse the mouse
        low_amplitude_mean = high_amplitude_mean
        # create the sound structure
        high_mat, low_mat = cloud_of_tones_matrices(
            **self.sound_properties_for_cot_mats,
            high_prob=high_perc,
            low_prob=low_perc,
            high_amplitude_mean=high_amplitude_mean,
            low_amplitude_mean=low_amplitude_mean,
        )
        # TODO: solve this in the calibration
        # Temporary solution: clip the loudness of every tone (non-zero values,
        # zeros are silence) to [bottom_amplitude_mean, top_amplitude_mean],
        # so that no tone falls outside the calibrated range.
        # Side effect: when the mean of the trial is close to one of the limits,
        # many tones are capped at that limit, so the real loudness spread is
        # smaller than amplitude_std. The saved auditory_stimulus has the clipped values.
        high_mat[high_mat != 0] = np.clip(
            high_mat[high_mat != 0],
            self.settings.bottom_amplitude_mean,
            self.settings.top_amplitude_mean,
            )
        low_mat[low_mat != 0] = np.clip(
            low_mat[low_mat != 0],
            self.settings.bottom_amplitude_mean,
            self.settings.top_amplitude_mean,
            )
        # store the trial stimuli
        self.trial_auditory_stimulus = {
            "high_tones": high_mat.to_dict(),
            "low_tones": low_mat.to_dict(),
        }
        self.trial_auditory_output_side = self.choose_auditory_output_side()

        # calibrate the sound for each speaker independently
        left_sound = self.generate_calibrated_sound_for_speaker(
            high_mat,
            low_mat,
            self.speakers["left"],
        )
        right_sound = self.generate_calibrated_sound_for_speaker(
            high_mat,
            low_mat,
            self.speakers["right"],
        )
        # silence one speaker if the sound is unilateral
        if self.trial_auditory_output_side == "left":
            right_sound = np.zeros_like(left_sound)
        elif self.trial_auditory_output_side == "right":
            left_sound = np.zeros_like(right_sound)

        # TODO: implement the relative to 1000 calibration

        self.set_trial_sound(left_sound, right_sound)

    def choose_auditory_output_side(self) -> str:
        """
        Speaker(s) that play the cloud of tones: "both", "left" or "right".
        With probability unilateral_sound_probability it is played from one side:
        unilateral_sound_side, or a random side if that setting is "both".
        """
        if random.random() < self.settings.unilateral_sound_probability:
            if self.settings.unilateral_sound_side in ["left", "right"]:
                return self.settings.unilateral_sound_side
            return random.choice(["left", "right"])
        return "both"

    def add_local_wn_stimulus(self) -> None:
        """
        Plays white noise only from the speaker of the reward side.
        Its loudness depends on the difficulty.
        """
        location_db_min, location_db_max = self.trial_difficulty_parameters[
            self.this_trial_difficulty
        ]["location_db_range"]

        sound_db = random.uniform(location_db_min, location_db_max)

        left_gain = self.calibrations.sound_calibration.get_sound_gain(
            self.speakers["left"],
            sound_db,
            "one_thousand_hz_calibration",
        )
        right_gain = self.calibrations.sound_calibration.get_sound_gain(
            self.speakers["right"],
            sound_db,
            "one_thousand_hz_calibration",
        )
        left_sound = white_noise(
            self.settings.loc_sound_duration,
            left_gain,
        )
        right_sound = white_noise(
            self.settings.loc_sound_duration,
            right_gain,
        )

        if self.this_trial_side == "left":
            right_sound = np.zeros_like(left_sound)
        else:
            left_sound = np.zeros_like(right_sound)

        self.trial_auditory_output_side = self.this_trial_side
        self.trial_auditory_stimulus = {
            "frequency_hz": "white_noise",
            "sound_db_spl": sound_db,
            "db_range_spl": [location_db_min, location_db_max],
            "duration": self.settings.loc_sound_duration,
        }
        self.set_trial_sound(left_sound, right_sound)

    def set_trial_sound(self, left_sound: np.ndarray, right_sound: np.ndarray) -> None:
        # store the sound so it is accessible by the softcode functions
        self.twoAFC_sound = {"left": left_sound, "right": right_sound}
        # load the sound to the Bpod in the ready_to_initiate state
        self.ready_to_initiate_output.append(Output.SoftCode2)
        # play the sound on the hold while stimulus state
        self.hold_while_stimulus_state_output.append(Output.SoftCode3)
        # the sound plays if not stopped TODO: test this explicitely

    def generate_calibrated_sound_for_speaker(
        self,
        high_mat: pd.DataFrame,
        low_mat: pd.DataFrame,
        speaker: int,
    ) -> np.ndarray:
        high_mat_calibrated = high_mat.map(
            lambda db: self.calibrations.sound_calibration.get_sound_gain(
                speaker,
                db,
                "one_thousand_hz_calibration",
            )
        )
        low_mat_calibrated = low_mat.map(
            lambda db: self.calibrations.sound_calibration.get_sound_gain(
                speaker,
                db,
                "one_thousand_hz_calibration",
            )
        )
        return sound_matrix_to_sound(
            pd.concat([high_mat_calibrated, low_mat_calibrated], axis=0),
            **self.sound_properties_for_sound_making,
        )

    
    def get_sound_from_settings(self) -> None:
        list_of_frequencies = np.logspace(
            np.log10(self.settings.lowest_frequency),
            np.log10(self.settings.highest_frequency),
            int(self.settings.number_of_frequencies * 3),
        ).round(0).tolist()
        low_freq_list = list_of_frequencies[: int(self.settings.number_of_frequencies)]
        high_freq_list = list_of_frequencies[-int(self.settings.number_of_frequencies) :]
        self.sound_properties_for_cot_mats = {
            "duration": self.settings.cot_sound_duration,
            "high_freq_list": high_freq_list,
            "low_freq_list": low_freq_list,
            "amplitude_std": self.settings.amplitude_std,
            "subduration": self.settings.tone_duration,
            "suboverlap": self.settings.tone_overlap,
        }
        self.sound_properties_for_sound_making = {
            "sample_rate": self.settings.sample_rate,
            "subduration": self.settings.tone_duration,
            "suboverlap": self.settings.tone_overlap,
            "ramp_time": self.settings.tone_ramp_time,
        }
    
    def get_performance_of_trial(self) -> bool | None:
        """
        This method calculates the performance of a trial, comparing the trial type
        to the first port that the mouse poked.
        - True / False: the first side poke was correct / incorrect.
        - False: early withdrawal from the center port that ended the trial
          (the stimulus state was never reached).
        - None: timeout, the mouse did not choose a side.
        You can access the trial information in self.trial_data
        """
        # early withdrawal: the trial ended before the stimulus state
        if not self.has_state_occurred("STATE_stimulus_state_START"):
            return False
        # get the side port that the mouse poked first
        first_poke = self.first_poke_after_stimulus_state()
        # timeout: no choice
        if first_poke is None:
            return None
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
        start_time = min(stim_state_array)
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

#     from training_protocol import TrainingProtocol

#     task = TwoAFC()
#     training = TrainingProtocol()
#     training.default_training_protocol()
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
