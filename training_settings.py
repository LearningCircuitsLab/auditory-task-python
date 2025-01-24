import numpy as np
from lecilab_behavior_analysis.utils import (get_session_number_of_trials,
                                             get_session_performance)
from village.classes.training import Training
from village.log import log

"""
Two Alternative Force Choice Task for the Training Village.

*First stage of training is Habituation Task. Here, center port lights up
and after poking both sides light up. Mouse receives reward for poking
in any port. This stage is used to habituate the mouse to the task.

*Second stage is TwoAFC Task using visual stimuli.
Here, center port lights up and after poking both ports light up with an easy discrimination.
Mouse receives reward for poking in the brightest port.

*Third stage is TwoAFC using visual stimuli with increased difficulty.
Both ports light up, but brightness can be more similar. Mouse receives reward for poking.

*Fourth stage is TwoAFC using auditory stimuli. Here, center port lights up and after poking
a cloud of tones is played. Mouse receives reward for poking in the correct port.

*Fifth stage is TwoAFC using auditory stimuli with increased difficulty.

*Sixth stage interleaves visual and auditory stimuli in easy mode. TODO: keep decreasing block size?

*Seventh stage interleaves visual and auditory stimuli in hard mode. TODO

Progression rules:
- Reward keeps decreasing after each session that has more than 50 trials.
- Animals move to TwoAFC (visual, easy) after 300 trials in Habituation.
- Waiting time in the center port keeps increasing to a limit during TwoAFC.
  This is implemented in the task, but parameters for how to do this are here.
- Animals move to the hard version of TwoAFC visual after after 3 consecutive 
  sessions with over 350 trials and with over 90% performance.
- Animals move to auditory version when they complete over 1000 trials on
  the hard version of the visual task.
- Animals move to the hard version of the auditory task is the same as the
  visual case.
"""


class TrainingSettings(Training):
    """
    This class defines how the training protocol is going to be.
    This is, how variables change depending on different conditions (e.g. performance),
    and/or which tasks are going to be run.

    In this class 2 methods need to be implemented:
    - __init__
    - update_training_settings

    In __init__ all the variables that can modify the state of the training protocol
    must be defined.
    When a new subject is created, a new row is added to the data/subjects.csv file,
    with these variables and its values.

    The following variables are needed:
    - self.next_task
    - self.refractary_period
    - self.minimum_duration
    - self.maximum_duration
    In addition to these variables, all the necessary variables to modify the state
    of the tasks can be included.

    When a task is run the values of the variables are read from the json file.
    When the task ends, the values of the variables are updated in the json file,
    following the logic in the update method.
    """

    def __init__(self) -> None:
        super().__init__()

    def default_training_settings(self) -> None:
        """
        This method is called when a new subject is created.
        It sets the default values for the training protocol.
        """
        # Settings in this block are mandatory for everything
        # that runs on Traning Village
        self.settings.next_task = "Habituation"
        self.settings.current_training_stage = "Habituation"
        self.settings.refractary_period = 14400
        self.settings.minimum_duration = 600
        self.settings.maximum_duration = 3600

        # Settings in this block are dependent on each task,
        # and the user needs to create and define them here

        # strength of the light in the middle port (0-1)
        self.settings.middle_port_light_intensity = 0.2
        # time the mouse needs to wait in the center port (in seconds)
        self.settings.holding_response_time_min = 0.03
        self.settings.holding_response_time_max = 0.5
        self.settings.holding_response_time_step = 0.001
        self.settings.holding_response_time = self.settings.holding_response_time_min
        # time the mouse has to respond (in seconds)
        self.settings.timer_for_response = 5
        # inter trial interval (in seconds)
        self.settings.iti = 1
        # reward amount in ml to start with (in ml)
        self.settings.reward_amount_ml = 5
        # will mouse be punished for incorrect responses? How long?
        self.settings.punishment = False
        self.settings.punishment_time = 1  # in seconds
        # stimulus modality
        self.settings.stimulus_modality = "visual"
        self.settings.stimulus_modality_block_size = 30
        # trial difficulty (e.g. ["easy", "medium", "hard"])
        self.settings.trial_difficulties = ["easy"]
        # turn on or off the anti-bias
        self.settings.anti_bias_on = False

        ## Things that should not be messed up with once they are settled on
        # trial sides (e.g. ["left", "right"]). Left always before right, for the bias
        self.settings.trial_sides = ["left", "right"]
        # parameters associated with trial difficulties
        self.settings.easy_light_intensity_difference = 5
        self.settings.easy_frequency_proportion = 98
        self.settings.medium_light_intensity_difference = 2.5
        self.settings.medium_frequency_proportion = 82
        self.settings.hard_light_intensity_difference = 1.25
        self.settings.hard_frequency_proportion = 66
        self.settings.trial_difficulty_parameters = {
            "easy": {
                "light_intensity_difference": self.settings.easy_light_intensity_difference,
                "frequency_proportion": self.settings.easy_frequency_proportion,
            },
            "medium": {
                "light_intensity_difference": self.settings.medium_light_intensity_difference,
                "frequency_proportion": self.settings.medium_frequency_proportion,
            },
            "hard": {
                "light_intensity_difference": self.settings.hard_light_intensity_difference,
                "frequency_proportion": self.settings.hard_frequency_proportion,
            },
        }
        # basic parameters about the stimuli
        # how many possible intensities can the incorrect side port have (eg. 0.15 - 0.33)*
        # * 0.33 can vary depending on the multiplier factor (eg. if 3 for easy),
        # as this multiplier will be the maximum intensity of the correct side port (max 1)
        self.settings.side_port_wrong_intensities_extremes = [0.01, 0.2]
        # TODO: how to deal with dictionaries in the settings?
        self.settings.auditory_contingency = {"left": "low", "right": "high"}
        # parameters for the auditory stimuli
        self.settings.sample_rate = 44100
        self.settings.sound_duration = 0.5
        self.settings.lowest_frequency = 5000
        self.settings.highest_frequency = 20000
        self.settings.number_of_frequencies = 6
        self.settings.tone_duration = 0.03
        self.settings.tone_overlap = 0.01
        self.settings.tone_ramp_time = 0.005
        self.settings.top_amplitude_mean = 70
        self.settings.bottom_amplitude_mean = 60
        self.settings.amplitude_std = 3

    def update_training_settings(self) -> None:
        """
        This method is called every time a session finishes.
        It is used to make the animal progress in the training protocol.
        """
        ## You have access to the following variables:
        # self.subject contains the name of the mouse
        # self.df object contains all data from training for a particular subject
        # self.settings contains the settings from the last session

        # General progressions and adjustments of parameters

        # decrease the reward amount for each session with more than 50 trials
        match np.sum(self.df.session.value_counts() > 50):
            case 0:
                self.settings.reward_amount_ml = 5
            case 1:
                self.settings.reward_amount_ml = 4
            case 2:
                self.settings.reward_amount_ml = 3.5
            case 3:
                self.settings.reward_amount_ml = 3
            case 4:
                self.settings.reward_amount_ml = 2.5
            case _:
                self.settings.reward_amount_ml = 2

        # update the waiting time in the center port during TwoAFC
        if self.settings.next_task == "TwoAFC":
            if "holding_time" in self.df.columns:
                self.settings.holding_response_time = self.df.iloc[-1]["holding_time"]

        # implement checks depending on the training stage
        match self.settings.current_training_stage:
            case "Habituation":
                self.check_progression_from_habituation()
            case "TwoAFC_visual_easy":
                self.check_progression_from_tafc_easy()
            case "TwoAFC_visual_hard":
                self.check_progression_from_tafc_visual_hard()
            case "TwoAFC_auditory_easy":
                self.check_progression_from_tafc_easy()
            case "TwoAFC_auditory_hard":
                self.check_progression_from_tafc_auditory_hard()
            case "Manual_training":
                # do nothing
                pass
            case _:
                # raise an error
                log.error(
                    f"Training stage {self.settings.current_training_stage} not recognized."
                )

        return None
    
    def define_gui_tabs(self) -> None:
        """
        This method is used to define the tabs that will be shown in the GUI.
        """
        self.gui_tabs = {
            "Visual": [
                "side_port_wrong_intensities_extremes",
                "easy_light_intensity_difference",
                "medium_light_intensity_difference",
                "hard_light_intensity_difference",
            ],
            "Sound": [
                "auditory_contingency",
                "easy_frequency_proportion",
                "medium_frequency_proportion",
                "hard_frequency_proportion",
                "sample_rate",
                "sound_duration",
                "lowest_frequency",
                "highest_frequency",
                "number_of_frequencies",
                "tone_duration",
                "tone_overlap",
                "tone_ramp_time",
                "top_amplitude_mean",
                "bottom_amplitude_mean",
                "amplitude_std",
            ],
            "Hide": [
                "holding_response_time",
                "trial_difficulty_parameters",
            ],

        }

        self.gui_tabs_restricted = {
            "current_training_stage": [
                "Habituation",
                "TwoAFC_visual_easy",
                "TwoAFC_visual_hard",
                "TwoAFC_auditory_easy",
                "TwoAFC_auditory_hard",
                "TwoAFC_multisensory_easy",
                "TwoAFC_multisensory_hard",
                "Manual_training",
            ],
            "stimulus_modality": ["visual", "auditory", "multisensory"],

        }


    def check_progression_from_habituation(self) -> None:
        """
        This method checks if the animal is ready to get promoted from habituation
        to the TwoAFC visual easy training stage.
        """
        # has the animal completed 300 trials?
        total_trials = self.df.shape[0]
        if total_trials >= 300:
            self.settings.next_task = "TwoAFC"
            self.settings.current_training_stage = "TwoAFC_visual_easy"
            self.settings.stimulus_modality = "visual"
            self.settings.trial_difficulties = ["easy"]
            # trigger alarm
            self.promotion_alarm()

        return None

    def check_progression_from_tafc_easy(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC easy to TwoAFC hard. Equal for both modalities.
        """
        # logic to promote the animal to the hard training stage:
        # after 3 consecutive sessions with over 350 trials and over 90% performance
        total_sessions = self.df.session.nunique()
        n_sessions = 3
        performance_threshold = 0.9
        if total_sessions >= n_sessions:
            previous_performances = [
                get_session_performance(self.df, session)
                for session in self.df.session.unique()[-n_sessions:]
            ]
            previous_n_trials = [
                get_session_number_of_trials(self.df, session)
                for session in self.df.session.unique()[-n_sessions:]
            ]
            if all(
                [
                    performance > performance_threshold
                    for performance in previous_performances
                ]
            ) and all([n_trials > 350 for n_trials in previous_n_trials]):
                # change the trial difficulty
                self.settings.trial_difficulties = ["easy", "medium", "hard"]
                # change training stage
                match self.settings.stimulus_modality:
                    case "visual":
                        self.settings.current_training_stage = "TwoAFC_visual_hard"
                    case "auditory":
                        self.settings.current_training_stage = "TwoAFC_auditory_hard"
                    case _:
                        # raise an error
                        log.error(
                            f"Stimulus modality {self.settings.stimulus_modality} not recognized."
                        )
                self.promotion_alarm()

        return None

    def check_progression_from_tafc_visual_hard(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC visual hard to TwoAFC auditory easy.
        """
        # logic to promote the animal to the auditory training stage:
        # after 1500 trials in the hard visual training stage
        total_trials = self.df[
            self.df.current_training_stage == "TwoAFC_visual_hard"
        ].shape[0]
        if total_trials >= 1500:
            self.settings.stimulus_modality = "auditory"
            self.settings.current_training_stage = "TwoAFC_auditory_easy"
            self.settings.trial_difficulties = ["easy"]
            self.promotion_alarm()

        return None

    def check_progression_from_tafc_auditory_hard(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC auditory hard to TwoAFC auditory easy.
        """
        # logic to promote the animal to the auditory training stage:
        # after 1500 trials in the hard auditory training stage
        total_trials = self.df[
            self.df.current_training_stage == "TwoAFC_auditory_hard"
        ].shape[0]
        if total_trials >= 1500:
            self.settings.current_training_stage = "TwoAFC_multisensory_easy"
            self.settings.trial_difficulties = ["easy"]
            self.settings.stimulus_modality = "multisensory"
            self.settings.stimulus_modality_block_size = 30
            self.promotion_alarm()

        return None

    def promotion_alarm(self) -> None:
        """
        This method is called when the animal is ready to move to the next stage.
        """
        log.alarm(
            subject=self.subject,
            description=f"Promotion to {self.settings.current_training_stage}",
        )
        return None


# # for debugging purposes
# if __name__ == "__main__":
#     import random

#     import pandas as pd

#     training = TrainingSettings()
#     dfdir = "/home/pi/Downloads/B15.csv"
#     training.df = pd.read_csv(dfdir, sep=";")
#     training.update_training_settings()

    # # create a new column of randomly picked boolean values
    # training.df["correct"] = [random.choice([True, False]) for _ in range(training.df.shape[0])]
    # # save it
    # training.df.to_csv(dfdir, sep=";", index=False)
