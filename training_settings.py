import numpy as np
from village.classes.training import Training

"""
Two Alternative Force Choice Task for the Training Village.

First stage of training is Habituation Task. Here, center port lights up
and after poking both sides light up. Mouse receives reward for poking
in any port. This stage is used to habituate the mouse to the task.

Second stage is TwoAFC Task using visual stimuli.
Here, center port lights up and after poking only one of the side ports lights up.
Mouse receives reward for poking in the correct port.

Third stage is TwoAFC using auditory stimuli. Here, center port lights up and after poking
a cloud of tones is played. Mouse receives reward for poking in the correct port.TODO


Progression rules:
- Reward keeps decreasing after each session that has more than 50 trials.
- Animals move to TwoAFC (visual, easy) after 300 trials in Habituation.
- Waiting time in the center port keeps increasing to a limit during TwoAFC.
  This is implemented in the task, but parameters for how to do this are here.
- Animals move to the hard version of TwoAFC visual after XXX. TODO
- Animals move to auditory version after 3 consecutive sessions on TwoAFC visual hard
  with over 350 trials and with over 90% performance.TODO
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
        self.settings.refractary_period = 14400
        self.settings.minimum_duration = 600
        self.settings.maximum_duration = 3600
        self.settings.maximum_number_of_trials = 10000

        # Settings in this block are dependent on each task,
        # and the user needs to create and define them here

        # strenght of the light in the middle port
        self.settings.middle_port_light_intensity = 50
        # time the mouse needs to wait in the center port
        self.settings.holding_response_time_min = .03
        self.settings.holding_response_time_max = .5
        self.settings.holding_response_time_step = .001
        self.settings.holding_response_time = self.settings.holding_response_time_min
        # time the mouse has to respond
        self.settings.timer_for_response = 5
        # inter trial interval
        self.settings.iti = 1
        # reward amount in ml to start with
        self.settings.reward_amount_ml = 5
        # will mouse be punished for incorrect responses? How long?
        self.settings.punishment = False
        self.settings.punishment_time = 1
        # stimulus modality
        self.settings.stimulus_modality = "visual"
        # trial types
        self.settings.trial_types = []
        # parameters associated with trial types
        self.settings.side_port_light_intensities = [100, 200]

    def update_training_settings(self) -> None:
        """
        This method is called every time a session finishes.
        It is used to make the animal progress in the training protocol.
        """
        ## You have access to the following variables:
        # self.subject contains the name of the mouse
        # self.df object contains all data from training for a particular subject
        # self.settings contains the settings from the last session

        # get some information
        total_trials = self.df.shape[0]
        total_sessions = len(self.df.session.unique())
        
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
        
        # progress to TwoAFC after 300 trials in Habituation
        if self.settings.next_task == "Habituation" and total_trials > 300:
            self.settings.next_task = "TwoAFC"
            self.settings.stimulus_modality = "visual"
            self.settings.trial_types = ["left_easy", "right_easy"]
        
        # update the waiting time in the center port during TwoAFC
        if self.settings.next_task == "TwoAFC":
            self.settings.holding_response_time = self.df.iloc[-1]["holding_time"]

        # logic to promote the animal to the second training stage:
        is_animal_in_hardest_stage = any(item in self.df.trial_type.unique() for item in ["left_hard", "right_hard"])
        if total_sessions >= 2 and not is_animal_in_hardest_stage:
            last_session_performance = self.get_session_performance(total_sessions)
            previous_session_performance = self.get_session_performance(total_sessions - 1)
            if last_session_performance >= 0.85 and previous_session_performance >= 0.85:
                # introduce punishment
                self.settings.punishment = True
                # change the trial types
                self.settings.trial_types = ["left_easy", "right_easy", "left_hard", "right_hard"]

        return None
    
    def get_session_performance(self, session: int) -> float:
        """
        This method calculates the performance of a session.
        """

        return self.df[self.df.session == session].correct.mean()

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