import numpy as np
from village.classes.training import Training
from village.log import log

from utils import get_session_number_of_trials, get_session_performance

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
a cloud of tones is played. Mouse receives reward for poking in the correct port.TODO

*Fifth stage is TwoAFC using auditory stimuli with increased difficulty. TODO

*Sixth stage interleaves visual and auditory stimuli in easy mode. TODO

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
    - self.maximum_number_of_trials
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
        # TODO: in the GUI, fix the values that stages can take
        self.settings.refractary_period = 14400
        self.settings.minimum_duration = 600
        self.settings.maximum_duration = 3600
        self.settings.maximum_number_of_trials = 10000

        # Settings in this block are dependent on each task,
        # and the user needs to create and define them here

        # strenght of the light in the middle port (0-1)
        self.settings.middle_port_light_intensity = .2
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
        self.settings.punishment_time = 1 # in seconds
        # stimulus modality
        self.settings.stimulus_modality = "visual"
        self.settings.stimulus_modality_block_size = 30
        # trial sides (e.g. ["left", "right"]). Left always before right, for the bias
        self.settings.trial_sides = ["left", "right"]
        # trial difficulty (e.g. ["easy", "medium", "hard"])
        self.settings.trial_difficulties = ["easy"]
        # turn on or off the anti-bias
        self.settings.anti_bias_on = False

        ## Things that should not be messed up with once they are settled on
        # parameters associated with trial difficulties
        self.settings.trial_difficulty_parameters = {
            "easy": {
                "light_intensity_difference": 0.5,
                "frequency_proportion": 98,
            },
            "medium": {
                "light_intensity_difference": 0.25,
                "frequency_proportion": 82,
            },
            "hard": {
                "light_intensity_difference": 0.1,
                "frequency_proportion": 66,
            },
        }
        # basic parameters about the stimuli
        # how many possible intensities can the side port have (0 - 0.6)*
        # * 0.6 can vary depending on the multiplier factor (above 0.5 for easy)
        self.settings.side_port_intensities_extremes = [0.05, 0.6]


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
            case _:
                # raise an error
                log.error(
                    f"Training stage {self.settings.current_training_stage} not recognized."
                )

        return None

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

        return None

    def check_progression_from_tafc_visual_hard(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC visual hard to TwoAFC auditory easy.
        """
        # logic to promote the animal to the auditory training stage:
        # after 1000 trials in the hard visual training stage
        total_trials = self.df[self.df.current_training_stage == "TwoAFC_visual_hard"].shape[0]
        if total_trials >= 1000:
            self.settings.stimulus_modality = "auditory"
            self.settings.current_training_stage = "TwoAFC_auditory_easy"
            self.settings.trial_difficulties = ["easy"]

        return None


# for debugging purposes
if __name__ == "__main__":
    import random

    import pandas as pd

    training = TrainingSettings()
    dfdir = "/home/pi/Downloads/B15.csv"
    training.df = pd.read_csv(dfdir, sep=";")
    training.update_training_settings()

    # # create a new column of randomly picked boolean values
    # training.df["correct"] = [random.choice([True, False]) for _ in range(training.df.shape[0])]
    # # save it
    # training.df.to_csv(dfdir, sep=";", index=False)
