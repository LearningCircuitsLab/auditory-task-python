# generate fake dataset for testing
import numpy as np
import pandas as pd


total_sessions = 25
starting_date = pd.to_datetime("2021-01-01")
current_training_stage_list = (
    ["Habituation"] * 3
    + ["TwoAFC_visual_easy"] * 5
    + ["TwoAFC_visual_hard"] * 3
    + ["TwoAFC_auditory_easy"] * 7
    + ["TwoAFC_auditory_hard"] * 4
    + ["TwoAFC_multisensory_easy"] * 8
)

# create empty dataframe
df = pd.DataFrame(
    columns=[
        "current_training_stage",
        "water",
        "correct_side",
        "stimulus_modality",
        "difficulty",
        "session",
        "correct",
        "holding_time",
        "date",
        "trial",
    ]
)

for i, session_counter in enumerate(np.arange(1, total_sessions + 1)):

    n_trials = np.random.randint(250, 500)

    trials = np.arange(1, n_trials + 1)
    # date
    date = [starting_date + pd.DateOffset(days=session_counter)] * n_trials
    # generate the trial types
    correct_side = np.random.choice(["left", "right"], n_trials)
    # generate the performance
    prob_correct = np.min([0.5 + 0.05 * session_counter, 0.99])
    correct = np.random.choice(
        [True, False], n_trials, p=[prob_correct, 1 - prob_correct]
    )
    # generate the holding time
    holding_time = np.random.choice([0.5, 1, 1.5, 2], n_trials)
    # stimulus modality
    if "visual" in current_training_stage_list[i]:
        stimulus_modality = "visual"
    elif "auditory" in current_training_stage_list[i]:
        stimulus_modality = "auditory"
    else:
        stimulus_modality = "multisensory"
    # difficulty
    if "hard" in current_training_stage_list[i]:
        difficulty = np.random.choice(["easy", "medium", "hard"], n_trials)
    else:
        difficulty = "easy"

    session = [session_counter] * n_trials

    # create the dataframe
    df_session = pd.DataFrame(
        {
            "current_training_stage": [current_training_stage_list[i]] * n_trials,
            "water": [2] * n_trials,
            "correct_side": correct_side,
            "stimulus_modality": [stimulus_modality] * n_trials,
            "difficulty": difficulty,
            "session": session,
            "correct": correct,
            "holding_time": holding_time,
            "date": date,
            "trial": trials,
        }
    )

    # concatenate the dataframes
    df = pd.concat([df, df_session])

# save the dataframe
df.to_csv(f"test-mouse_fake_data.csv", sep=";", index=False)
