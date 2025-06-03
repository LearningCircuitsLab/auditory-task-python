import numpy as np
import lecilab_behavior_analysis.utils as utils
from village.classes.training import Training
from village.log import log
from village.settings import settings

"""
Two Alternative Force Choice Task for the Training Village.

*First stage of training is Habituation Task. Here, center port lights up
and after poking both sides light up. Mouse receives reward for poking
in any port. This stage is used to habituate the mouse to the task.
TODO:
- remove the water at the beginning after a few sessions
- remove the auto water after 2 minutes

*Second stage is TwoAFC Task using visual stimuli.
Here, center port lights up and after poking, both ports light up with an easy discrimination.
Mouse receives reward for poking in the brightest port.

*Third stage is TwoAFC using visual stimuli with increased difficulty.
Both ports light up, but brightness can be more similar. Mouse receives reward for poking.

*Fourth stage is TwoAFC using auditory stimuli. Here, center port lights up and after poking,
a cloud of tones is played. Mouse receives reward for poking in the correct port.

*Fifth stage is TwoAFC using auditory stimuli with increased difficulty.

*Sixth stage interleaves visual and auditory stimuli in easy mode in blocks.

*Seventh stage interleaves visual and auditory stimuli in hard mode in blocks.

Progression rules:
- Reward keeps decreasing after each session that has more than 50 trials.
- Animals move to TwoAFC (visual, easy) after 300 trials in Habituation.
- Waiting time in the center port keeps increasing to a limit during TwoAFC.
  This is implemented in the task, but parameters for how to do this are here.
- Animals move to the hard version of TwoAFC visual after after 3 consecutive 
  days with over 500 trials and with over 85% performance.
- Animals move to auditory version when they complete over 1500 trials on
  the hard version of the visual task.
- Animals move to the hard version of the auditory task is the same as the
  visual case.
- Animals move to the multisensory task after completing 1500 trials on the
  hard version of the auditory task.
- Animals move to the hard version of the multisensory task is the same as the
  visual and auditory case.
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
    - self.refractory_period
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
        self.settings.refractory_period = 2*60*60 # 2 hours
        self.settings.minimum_duration = 10*60 # 10 minutes
        self.settings.maximum_duration = 30*60 # 30 minutes

        # Settings in this block are dependent on each task,
        # and the user needs to create and define them here
        # stimulus modality
        self.settings.stimulus_modality = "visual"
        self.settings.stimulus_modality_block_size = 70
        # strength of the light in the middle port (0-1)
        self.settings.middle_port_light_intensity = 0.2
        # time that, in Habituation, the trial ends and reward is automatically delivered (in seconds)
        self.settings.time_to_auto_reward = 120
        self.settings.initial_large_reward = True
        # time the mouse needs to wait in the center port in 2AFC (in seconds)
        self.settings.holding_response_time_min = 0.05
        self.settings.holding_response_time_max = 0.5
        self.settings.holding_response_time_step = 0.001
        self.settings.holding_response_time = self.settings.holding_response_time_min
        # time the mouse has to respond (in seconds)
        self.settings.timer_for_response = 50
        # reward amount in ml to start with (in ml)
        self.settings.reward_amount_ml = 5
        # inter trial interval (in seconds)
        # will mouse be punished for incorrect responses? How long?
        self.settings.punishment = False
        self.settings.punishment_time = 1  # in seconds
        self.settings.iti = 1
        # trial difficulties
        self.settings.easy_trials_on = True
        self.settings.medium_trials_on = False
        self.settings.hard_trials_on = False
        # turn on or off the anti-bias
        self.settings.anti_bias_on = True
        self.settings.anti_bias_vector_size = 10

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
        # basic parameters about the stimuli
        # how many possible intensities can the incorrect side port have (eg. 0.15 - 0.33)*
        # * 0.33 can vary depending on the multiplier factor (eg. if 3 for easy),
        # as this multiplier will be the maximum intensity of the correct side port (max 1)
        self.settings.side_port_wrong_intensities_extremes = [0.01, 0.2]
        # contingency
        self.settings.frequency_associated_with_left_choice = "high"
        # parameters for the auditory stimuli
        # TODO: make an example for how to access this value
        self.settings.sample_rate = settings.get("SAMPLERATE")
        self.settings.sound_duration = 0.5
        self.settings.lowest_frequency = 5000
        self.settings.highest_frequency = 40000
        self.settings.number_of_frequencies = 6
        self.settings.tone_duration = 0.03
        self.settings.tone_overlap = 0.01
        self.settings.tone_ramp_time = 0.005
        self.settings.top_amplitude_mean = 70
        self.settings.bottom_amplitude_mean = 60
        self.settings.amplitude_std = 2
        self.settings.ambiguous_beginning_time = 0.05

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

        # if the animal is running on manual mode and the training stage is manual, keep the same settings
        if self.df.run_mode.iloc[-1] == "Manual" and self.settings.current_training_stage == "Manual_training":
            return None

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
            case "TwoAFC_multisensory_easy":
                self.check_progression_from_tafc_easy()
            case "TwoAFC_multisensory_hard":
                self.check_progression_from_tafc_multisensory_hard()
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
            "Difficulty": [
                "easy_trials_on",
                "medium_trials_on",
                "hard_trials_on",
            ],
            "Habituation": [
                "initial_large_reward",
                "time_to_auto_reward",
            ],
            "Visual": [
                "side_port_wrong_intensities_extremes",
                "easy_light_intensity_difference",
                "medium_light_intensity_difference",
                "hard_light_intensity_difference",
            ],
            "Sound": [
                "frequency_associated_with_left_choice",
                "easy_frequency_proportion",
                "medium_frequency_proportion",
                "hard_frequency_proportion",
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
                "ambiguous_beginning_time",
            ],
            "Hide": [
                "trial_sides",
                "sample_rate",
                "holding_response_time",
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
            "punishment": [True, False],
            "anti_bias_on": [True, False],
            "easy_trials_on": [True, False],
            "medium_trials_on": [True, False],
            "hard_trials_on": [True, False],
            "frequency_associated_with_left_choice": ["low", "high"],
            "initial_large_reward": [True, False],
        }


    def check_progression_from_habituation(self) -> None:
        """
        This method checks if the animal is ready to get promoted from habituation
        to the TwoAFC visual easy training stage.
        """
        # remove the automatic water at the beginning after a few sessions
        total_sessions = self.df.session.nunique()
        if total_sessions >= 4:
            self.settings.initial_large_reward = False
            # add 20 seconds to the auto reward time for each session
            self.settings.time_to_auto_reward += 20

            # increase min time and refractory period (4 hours)
            self.increase_min_time_and_refractory_period(
                minimum_duration_max=20*60,
                refractory_period_max=3*60*60,
                maximum_duration_max=40*60,
            )

        # has the animal completed 300 trials?
        total_trials = self.df.shape[0]
        if total_trials >= 300:
            self.settings.next_task = "TwoAFC"
            self.settings.current_training_stage = "TwoAFC_visual_easy"
            self.settings.stimulus_modality = "visual"
            self.settings.easy_trials_on = True
            # trigger alarm
            self.promotion_alarm()

        return None

    def check_progression_from_tafc_easy(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC easy to TwoAFC hard. Equal for both modalities and multisensory.
        """
        # logic to promote the animal to the hard training stage:
        # after 3 consecutive days with over 500 trials and over 85% performance
        # it also introduces punishment if performance is above 70% after 3 days
        n_days = 3
        promotion_performance_threshold = 0.85
        promotion_ntrials_threshold = 500
        punishment_performance_threshold = 0.70

        df_with_day = self.df.copy()
        df_with_day["year_month_day"] = df_with_day.date.astype('datetime64[ns]').dt.strftime("%Y-%m-%d")
        total_days = df_with_day[df_with_day.current_training_stage == self.settings.current_training_stage].year_month_day.nunique()

        if total_days >= 3:
            self.increase_min_time_and_refractory_period(
                minimum_duration_max=25*60,
                refractory_period_max=4*60*60,
                maximum_duration_max=50*60,
            )

        if total_days >= n_days:
            previous_performances = [
                utils.get_day_performance(df_with_day, day)
                for day in df_with_day.year_month_day.unique()[-n_days:]
            ]
            previous_n_trials = [
                utils.get_day_number_of_trials(df_with_day, day)
                for day in df_with_day.year_month_day.unique()[-n_days:]
            ]
            # introduce punishment if conditions are met
            if all(
                [
                    performance > punishment_performance_threshold
                    for performance in previous_performances
                ]
            ):
                self.settings.punishment = True
                self.settings.punishment_time = 1
            # check if the animal is ready to be promoted
            if all(
                [
                    performance > promotion_performance_threshold
                    for performance in previous_performances
                ]
            ) and all([n_trials > promotion_ntrials_threshold for n_trials in previous_n_trials]):
                # change the trial difficulty
                self.settings.easy_trials_on = True
                self.settings.medium_trials_on = True
                self.settings.hard_trials_on = True
                # change training stage
                match self.settings.stimulus_modality:
                    case "visual":
                        self.settings.current_training_stage = "TwoAFC_visual_hard"
                    case "auditory":
                        self.settings.current_training_stage = "TwoAFC_auditory_hard"
                    case "multisensory":
                        self.settings.current_training_stage = "TwoAFC_multisensory_hard"
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
        # after 1500 trials in the hard visual training stage,
        # with no performance requirements
        total_trials = self.df[
            self.df.current_training_stage == "TwoAFC_visual_hard"
        ].shape[0]
        if total_trials >= 1500:
            self.settings.stimulus_modality = "auditory"
            self.settings.current_training_stage = "TwoAFC_auditory_easy"
            self.settings.easy_trials_on = True
            self.settings.medium_trials_on = False
            self.settings.hard_trials_on = False
            self.promotion_alarm()

        return None

    def check_progression_from_tafc_auditory_hard(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC auditory hard to TwoAFC multisensory easy.
        """
        # logic to promote the animal to the auditory training stage:
        # after 1500 trials in the hard auditory training stage
        total_trials = self.df[
            self.df.current_training_stage == "TwoAFC_auditory_hard"
        ].shape[0]
        if total_trials >= 1500:
            self.settings.current_training_stage = "TwoAFC_multisensory_easy"
            self.settings.easy_trials_on = True
            self.settings.medium_trials_on = False
            self.settings.hard_trials_on = False
            self.settings.stimulus_modality = "multisensory"
            self.promotion_alarm()

        return None

    def check_progression_from_tafc_multisensory_hard(self) -> None:
        # Last stage, no progression, for now
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
    
    def increase_min_time_and_refractory_period(
            self,
            minimum_duration_max = 2400,
            refractory_period_max = 28800,
            maximum_duration_max = 3600,
        ) -> None:
        # increase the min time of the session 1 minutes for each session
        # with a limit
        self.settings.minimum_duration = min(
            self.settings.minimum_duration + 60, minimum_duration_max
        )
        # increase the refractory period 5 minutes for each session with
        # a limit
        self.settings.refractory_period = min(
            self.settings.refractory_period + 5*60, refractory_period_max
        )
        # increase the maximum duration 1 minutes for each session with
        # a limit
        self.settings.maximum_duration = min(
            self.settings.maximum_duration + 60, maximum_duration_max
        )


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
