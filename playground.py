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
