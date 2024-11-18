# generate fake dataset for testing
import numpy as np
import pandas as pd

total_trials_by_session = [
    23,  # session 1
    25,  # session 2
    60,  # session 3
    50,  # session 4
    112,  # session 5
    150,  # session 6
    200,  # session 7
    250,  # session 8
    300,  # session 9
    350,  # session 10
]

# create empty dataframe
df = pd.DataFrame(columns=[
    "session",
    "trial_type",
    "correct",
    "holding_time",
    ])

session_counter = 1
for n_trials in total_trials_by_session:
    # generate the trial types
    trial_types = np.random.choice(["left", "right"], n_trials)
    # generate the performance
    prob_correct = np.min([0.5 + 0.05 * session_counter, 0.99])
    correct = np.random.choice([True, False], n_trials, p=[prob_correct, 1 - prob_correct])
    # generate the holding time
    holding_time = np.random.choice([0.5, 1, 1.5, 2], n_trials)
    # create the dataframe
    df_session = pd.DataFrame({
        "session": [session_counter] * n_trials,
        "trial_type": trial_types,
        "correct": correct,
        "holding_time": holding_time,
        })
    session_counter += 1

    # concatenate the dataframes
    df = pd.concat([df, df_session])

# save the dataframe
df.to_csv(f"fake_data.csv", sep=";", index=False)
