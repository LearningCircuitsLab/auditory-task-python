import numpy as np
import pandas as pd
import lecilab_behavior_analysis.utils as utils
from village.custom_classes.training_protocol_base import TrainingProtocolBase
from village.scripts.log import log
from village.settings import settings

"""
Two Alternative Force Choice Task for the Training Village.

Stages:
- Habituation: the center port lights up; after poking it, both side ports
  light up and both give reward. From the 4th session on, the initial large
  reward is removed, the time before the automatic reward
  (time_to_auto_reward) grows by 20 s per session, and the session durations
  and refractory period grow slowly.
- TwoAFC_<modality>_easy: only easy trials.
- TwoAFC_<modality>_hard: easy, medium and hard trials.

The modalities and their order come from the training sequence: first,
second and third_stimulus_modality in the GUI (second and third are
optional). The third can only be multisensory, which alternates the
modalities before it in blocks.

Progression rules:
- Habituation -> first modality, easy: after 150 trials in total.
- Easy -> hard (same modality), using only the trials of the current stage:
  the last 3 days each with over 85% performance and over 100 trials.
  Punishment is switched on if the last 3 days are all above 70%, or if
  the last 5 days are all below 60% (checked from the 5th day in the stage).
  From the 3rd day in the stage, session durations and refractory period
  grow slowly.
- Hard -> next modality of the sequence, easy: after
  <modality>_hard_trials_to_promote trials in the hard stage (one setting
  per single modality), with no performance requirement. If that setting
  is 0, the hard stage is skipped: the animal goes from the easy stage
  straight to the next modality. Punishment is switched off and the
  anti-bias on. If there is no next modality, the animal stays in the hard
  stage. Multisensory hard is always the last stage.
- The holding time in the center port grows by holding_response_time_step
  on each correct trial, up to holding_response_time_max (done in the task).
  It carries over from one session to the next.
"""

## Modalities and training stages
# Single source of truth for the modalities, shared with twoAFC.py.
# Modality names use hyphens (never underscores), because underscores separate
# the parts of a stage name: TwoAFC_<modality>_<difficulty>
# Modalities in which one single stimulus type tells the mouse where the reward is
SINGLE_MODALITIES = ("visual", "auditory-cot", "auditory-local-wn")
# Modality that alternates, in blocks, the single modalities of the training sequence
MULTISENSORY = "multisensory"
ALL_MODALITIES = SINGLE_MODALITIES + (MULTISENSORY,)
# Difficulties that are part of a stage name
STAGE_DIFFICULTIES = ("easy", "hard")
# Value of the modality dropdowns in the GUI when that position is not used
NO_MODALITY = "none"
# Setting with the trials needed in the hard stage of each single modality to
# move to the next modality of the sequence (0: skip the hard stage).
# Multisensory has none: it is always the last stage.
HARD_TRIALS_TO_PROMOTE_SETTINGS = {
    "visual": "visual_hard_trials_to_promote",
    "auditory-cot": "auditory_cot_hard_trials_to_promote",
    "auditory-local-wn": "auditory_local_wn_hard_trials_to_promote",
}


def get_stage_name(modality: str, difficulty: str) -> str:
    return f"TwoAFC_{modality}_{difficulty}"


def parse_stage(stage: str) -> tuple[str, str]:
    """
    Returns (modality, difficulty) of a TwoAFC stage name,
    e.g. "TwoAFC_auditory-cot_easy" -> ("auditory-cot", "easy").
    Raises ValueError if the stage is not a TwoAFC stage.
    """
    parts = stage.split("_")
    if (
        len(parts) != 3
        or parts[0] != "TwoAFC"
        or parts[1] not in ALL_MODALITIES
        or parts[2] not in STAGE_DIFFICULTIES
    ):
        raise ValueError(f"{stage} is not a valid TwoAFC training stage")
    return parts[1], parts[2]


def get_training_sequence(settings) -> list[str]:
    """
    Builds the training sequence from the modality dropdowns of the GUI
    (first, second and third_stimulus_modality). Second and third are optional
    (value "none"). Raises ValueError if the combination is not valid.
    """
    first = settings.first_stimulus_modality
    second = settings.second_stimulus_modality
    third = settings.third_stimulus_modality

    if first not in SINGLE_MODALITIES:
        raise ValueError(
            f"first_stimulus_modality must be one of {SINGLE_MODALITIES}, got {first}"
        )
    sequence = [first]

    if second != NO_MODALITY:
        if second not in SINGLE_MODALITIES:
            raise ValueError(
                f"second_stimulus_modality must be one of {SINGLE_MODALITIES} "
                f"or '{NO_MODALITY}', got {second}"
            )
        if second == first:
            raise ValueError("first and second stimulus modalities must be different")
        sequence.append(second)

    if third != NO_MODALITY:
        if third != MULTISENSORY:
            raise ValueError(
                f"third_stimulus_modality must be '{MULTISENSORY}' "
                f"or '{NO_MODALITY}', got {third}"
            )
        if len(sequence) < 2:
            raise ValueError(
                "multisensory needs two different single modalities before it"
            )
        sequence.append(third)

    return sequence


def get_block_modalities(sequence: list[str]) -> list[str]:
    """Single modalities that alternate in blocks in the multisensory stage."""
    return [modality for modality in sequence if modality != MULTISENSORY]


class TrainingProtocol(TrainingProtocolBase):
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

        # Training sequence assigned to this animal (see get_training_sequence).
        # Second and third are optional ("none").
        self.settings.first_stimulus_modality = "visual"
        self.settings.second_stimulus_modality = "auditory-cot"
        self.settings.third_stimulus_modality = MULTISENSORY

        # Settings in this block are dependent on each task,
        # and the user needs to create and define them here
        # The modality of a session comes from current_training_stage
        # (TwoAFC_<modality>_<difficulty>). This setting is ONLY used when
        # current_training_stage is "Manual_training"
        self.settings.manual_training_modality = "visual"
        self.settings.stimulus_modality_block_size = 70
        # strength of the light in the middle port (0-1)
        self.settings.middle_port_light_intensity = 0.05
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
        # reward amount per correct trial (in µl, as the water calibration)
        self.settings.reward_amount_ul = 3
        # inter trial interval (in seconds)
        # will mouse be punished for incorrect responses? How long?
        self.settings.punishment = False
        self.settings.punishment_time = 3  # in seconds
        # will it be punished for poking out of the center port early?
        self.settings.early_poke_punishment = False
        # time between trials (in seconds)
        self.settings.iti = 1
        # trial difficulties
        self.settings.easy_trials_on = True
        self.settings.medium_trials_on = False
        self.settings.hard_trials_on = False
        # trials needed in the hard stage of each modality to move to the next
        # modality of the sequence. 0: the hard stage is skipped (if there is a
        # next modality). Multisensory hard is always the last stage
        self.settings.visual_hard_trials_to_promote = 1000
        self.settings.auditory_cot_hard_trials_to_promote = 1000
        self.settings.auditory_local_wn_hard_trials_to_promote = 1000
        # turn on or off the anti-bias
        self.settings.anti_bias_on = True
        self.settings.anti_bias_vector_size = 10

        ## Things that should not be messed up with once they are settled on
        # trial sides (e.g. ["left", "right"]). Left always before right, for the bias
        self.settings.trial_sides = ["left", "right"]
        # parameters associated with trial difficulties
        self.settings.easy_light_intensity_difference = 6
        self.settings.easy_frequency_proportion = 98
        self.settings.medium_light_intensity_difference = 4
        self.settings.medium_frequency_proportion = 82
        self.settings.hard_light_intensity_difference = 2
        self.settings.hard_frequency_proportion = 66
        self.settings.easy_location_db_range = [60, 70]
        self.settings.medium_location_db_range = [50, 60]
        self.settings.hard_location_db_range = [40, 50]

        # basic parameters about the stimuli
        # how many possible intensities can the incorrect side port have (eg. 0.15 - 0.33)*
        # * 0.33 can vary depending on the multiplier factor (eg. if 3 for easy),
        # as this multiplier will be the maximum intensity of the correct side port (max 1)
        self.settings.side_port_wrong_intensities_extremes = [0.01, 0.1666]
        # distractors: present an uninformative stimulus of this type in trials
        # whose modality is a different one (never randomizes the cue itself)
        # random light in non-visual trials
        self.settings.random_visual_stimulus = False
        # random cloud of tones in visual trials (never in white noise trials)
        self.settings.random_COT_stimulus = False
        # contingency
        self.settings.frequency_associated_with_left_choice = "high"
        # parameters for the auditory stimuli
        # TODO: make an example for how to access this value
        self.settings.sample_rate = settings.get("SAMPLERATE")
        # duration of the white noise of the sound location modality
        self.settings.loc_sound_duration = 0.1
        # duration of the cloud of tones
        self.settings.cot_sound_duration = 0.5
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
        # probability that the cloud of tones is played from one speaker only,
        # and from which one ("both" means a random side each time)
        self.settings.unilateral_sound_probability = 0
        self.settings.unilateral_sound_side = "both"

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
        # validate the training sequence chosen in the GUI (raises if not valid)
        get_training_sequence(self.settings)
        # if the animal is running on manual mode and the training stage is manual, keep the same settings
        if self.df.run_mode.iloc[-1] == "Manual" and self.settings.current_training_stage == "Manual_training":
            return None

        # decrease the reward amount for each session with more than 50 trials
        # match np.sum(self.df.session.value_counts() > 50):
            # case 0:
            #     self.settings.reward_amount_ul = 5
            # case 1:
            #     self.settings.reward_amount_ul = 4
            # case 2:
            #     self.settings.reward_amount_ul = 3.5
            # case 3:
            #     self.settings.reward_amount_ul = 3
            # case 4:
            #     self.settings.reward_amount_ul = 2.5
            # case _:
            #     self.settings.reward_amount_ul = 2

        # update the waiting time in the center port during TwoAFC
        if self.settings.next_task == "TwoAFC":
            if "holding_time" in self.df.columns:
                # use the last saved value; rows of other tasks (e.g. Habituation)
                # have no holding time, so they are skipped
                previous_holding_times = pd.to_numeric(
                    self.df["holding_time"], errors="coerce"
                ).dropna()
                if previous_holding_times.empty:
                    self.settings.holding_response_time = (
                        self.settings.holding_response_time_min
                    )
                else:
                    self.settings.holding_response_time = float(
                        previous_holding_times.iloc[-1]
                    )

        # implement checks depending on the training stage
        stage = self.settings.current_training_stage

        if stage == "Habituation":
            self.check_progression_from_habituation()
            return None

        if stage == "Manual_training":
            return None

        try:
            _, difficulty = parse_stage(stage)
        except ValueError:
            log.error(f"Training stage {stage} not recognized.")
            return None

        if difficulty == "easy":
            self.check_progression_from_tafc_easy()
        elif difficulty == "hard":
            self.check_progression_from_tafc_hard()

        return None


    def define_gui_tabs(self) -> None:
        """
        This method is used to define the tabs that will be shown in the GUI.
        """
        self.gui_tabs = {
            "Protocol": [
                "first_stimulus_modality",
                "second_stimulus_modality",
                "third_stimulus_modality",
            ],
            "Difficulty": [
                "easy_trials_on",
                "medium_trials_on",
                "hard_trials_on",
                "visual_hard_trials_to_promote",
                "auditory_cot_hard_trials_to_promote",
                "auditory_local_wn_hard_trials_to_promote",
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
                "random_visual_stimulus",
            ],
            # only used when current_training_stage is "Manual_training"
            "Manual training only": [
                "manual_training_modality",
            ],
            "Sound COT": [
                "ambiguous_beginning_time",
                "frequency_associated_with_left_choice",
                "easy_frequency_proportion",
                "medium_frequency_proportion",
                "hard_frequency_proportion",
                "cot_sound_duration",
                "lowest_frequency",
                "highest_frequency",
                "number_of_frequencies",
                "tone_duration",
                "tone_overlap",
                "tone_ramp_time",
                "top_amplitude_mean",
                "bottom_amplitude_mean",
                "amplitude_std",
                "unilateral_sound_probability",
                "unilateral_sound_side",
                "random_COT_stimulus",
            ],
            "Sound loc": [
                "loc_sound_duration",
                "easy_location_db_range",
                "medium_location_db_range",
                "hard_location_db_range",
            ],
            "Hide": [
                "trial_sides",
                "sample_rate",
                "holding_response_time",
            ],
        }

        self.gui_tabs_restricted = {
            "first_stimulus_modality": list(SINGLE_MODALITIES),
            "second_stimulus_modality": list(SINGLE_MODALITIES) + [NO_MODALITY],
            "third_stimulus_modality": [MULTISENSORY, NO_MODALITY],
            "current_training_stage": (
                ["Habituation"]
                + [
                    get_stage_name(modality, difficulty)
                    for modality in ALL_MODALITIES
                    for difficulty in STAGE_DIFFICULTIES
                ]
                + ["Manual_training"]
            ),
            "manual_training_modality": list(ALL_MODALITIES),
            "punishment": [True, False],
            "early_poke_punishment": [True, False],
            "anti_bias_on": [True, False],
            "easy_trials_on": [True, False],
            "medium_trials_on": [True, False],
            "hard_trials_on": [True, False],
            "frequency_associated_with_left_choice": ["low", "high"],
            "initial_large_reward": [True, False],
            "random_COT_stimulus": [False, True],
            "random_visual_stimulus": [False, True],
            "unilateral_sound_side": ["both", "left", "right"],
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
        if total_trials >= 150:
            self.settings.next_task = "TwoAFC"

            first_modality = get_training_sequence(self.settings)[0]

            self.settings.current_training_stage = get_stage_name(
                modality=first_modality, difficulty="easy"
            )

            self.settings.easy_trials_on = True
            self.settings.medium_trials_on = False
            self.settings.hard_trials_on = False
            self.settings.punishment = False

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
        promotion_ntrials_threshold = 100
        punishment_performance_threshold = 0.70

        # if the animal has failed 5 consecutive days with performance below 60%, introduce punishment
        # They may bias so much and have no motivation to do the task
        n_days_fail = 5
        fail_performance_threshold = 0.60

        # only the trials of the current stage count: days, performance and
        # number of trials (other stages, Habituation or other tasks on the
        # same day are left out)
        df_with_day = self.df[
            self.df.current_training_stage == self.settings.current_training_stage
        ].copy()
        df_with_day["year_month_day"] = df_with_day.date.astype('datetime64[ns]').dt.strftime("%Y-%m-%d")
        total_days = df_with_day.year_month_day.nunique()

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
                self.settings.punishment_time = 3
            
            
            # check if the animal is ready to be promoted
            if all(
                [
                    performance > promotion_performance_threshold
                    for performance in previous_performances
                ]
            ) and all([n_trials > promotion_ntrials_threshold for n_trials in previous_n_trials]):
                modality, _ = parse_stage(self.settings.current_training_stage)
                next_modality = self.get_next_modality(modality)
                # skip the hard stage if its number of trials is 0
                # and there is a next modality
                if (
                    self.get_hard_trials_to_promote(modality) == 0
                    and next_modality is not None
                ):
                    self.promote_to_modality(next_modality)
                else:
                    # change the trial difficulty
                    self.settings.easy_trials_on = True
                    self.settings.medium_trials_on = True
                    self.settings.hard_trials_on = True
                    # change training stage
                    self.settings.current_training_stage = get_stage_name(
                        modality=modality, difficulty="hard"
                    )
                    self.promotion_alarm()
                
        if total_days >= n_days_fail:
            previous_performances = [
                utils.get_day_performance(df_with_day, day)
                for day in df_with_day.year_month_day.unique()[-n_days_fail:]
            ]
            # introduce punishment if conditions are not met
            if all(
                [
                    performance < fail_performance_threshold
                    for performance in previous_performances
                ]
            ):
                self.settings.punishment = True
                self.settings.punishment_time = 3

        return None

    def check_progression_from_tafc_hard(self) -> None:
        """
        This method checks if the animal is ready to get promoted from
        TwoAFC hard to the next modality in the training sequence.
        """
        # logic to promote the animal to the next modality in the training sequence:
        # after <modality>_hard_trials_to_promote trials in the hard training stage,
        # with no performance requirements. Multisensory hard is the last stage
        modality, _ = parse_stage(self.settings.current_training_stage)
        if modality == MULTISENSORY:
            return None
        next_modality = self.get_next_modality(modality)
        if next_modality is None:
            # last modality of the sequence, or not in the sequence
            return None

        total_trials = self.df[
            self.df.current_training_stage == self.settings.current_training_stage
        ].shape[0]
        if total_trials >= self.get_hard_trials_to_promote(modality):
            self.promote_to_modality(next_modality)

        return None

    def get_hard_trials_to_promote(self, modality: str) -> int | None:
        """Trials needed in the hard stage of a modality (None for multisensory)."""
        setting_name = HARD_TRIALS_TO_PROMOTE_SETTINGS.get(modality)
        if setting_name is None:
            return None
        return getattr(self.settings, setting_name)

    def get_next_modality(self, modality: str) -> str | None:
        """
        Next modality of the training sequence, or None if this is the last one.
        The position in the sequence is derived from the stage, not stored.
        """
        sequence = get_training_sequence(self.settings)
        if modality not in sequence:
            log.alarm(
                subject=self.subject,
                description=(
                    f"Stage {self.settings.current_training_stage} uses modality "
                    f"{modality}, which is not in the training sequence {sequence}. "
                    "The animal will not be promoted to another modality."
                ),
            )
            return None
        sequence_index = sequence.index(modality)
        if sequence_index == len(sequence) - 1:
            return None
        return sequence[sequence_index + 1]

    def promote_to_modality(self, modality: str) -> None:
        """Moves the animal to the easy stage of a new modality."""
        self.settings.current_training_stage = get_stage_name(
            modality=modality, difficulty="easy"
        )
        self.settings.easy_trials_on = True
        self.settings.medium_trials_on = False
        self.settings.hard_trials_on = False
        self.settings.punishment = False
        self.settings.anti_bias_on = True
        self.promotion_alarm()

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

#     training = TrainingProtocol()
#     dfdir = "/home/pi/Downloads/B15.csv"
#     training.df = pd.read_csv(dfdir, sep=";")
#     training.update_training_settings()

    # # create a new column of randomly picked boolean values
    # training.df["correct"] = [random.choice([True, False]) for _ in range(training.df.shape[0])]
    # # save it
    # training.df.to_csv(dfdir, sep=";", index=False)
