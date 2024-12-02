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
# %%# %%