# %%
import numpy as np
import pandas as pd

# %%
# open fake data
df = pd.read_csv("fake_data.csv", sep=";")
# %%
print(df.head())
# %%
np.sum(df.session.value_counts() > 50)
# %%
total_sessions = df.session.nunique()
[x for x in df.session.unique()[-3:]]
# %%
# I want to get true/false following an exponential distribution so that the
# probability of getting a True is 0.05
np.sum(np.random.exponential(30, 10000) < 30) / 10000


# %%
import matplotlib.pyplot as plt

plt.hist(np.random.exponential(30, 10000), bins=100)
# %%
# from chatgpt
n_samples = 10000
lower_bound = 20
upper_bound = 50
optimal_lambda = 0.0607
u = np.random.uniform(0, 1, n_samples)  # Uniform samples
samples = (
    lower_bound
    - np.log(1 - u * (1 - np.exp(-optimal_lambda * (upper_bound - lower_bound))))
    / optimal_lambda
)

plt.hist(samples, bins=100)
plt.show()

#
# # %%
# %%
import numpy as np

np.random.uniform(0, 1)
# %%
