# %%
import numpy as np
import pandas as pd
from sound_functions import cloud_of_tones
# %%
lowest_freq = 5000
highest_freq = 20000
freqs_log_spaced = np.round(np.logspace(np.log10(lowest_freq), np.log10(highest_freq), 18)).tolist()
low_freqs = freqs_log_spaced[:6]
high_freqs = freqs_log_spaced[-6:]
# Define sound properties
sound_properties = {
    "sample_rate": 48000,
    "duration": .5,
    "ramp_time": 0.005,
    "high_amplitude_mean": 60,
    "low_amplitude_mean": 70,
    "amplitude_std": 2,
    "high_freq_list": high_freqs,
    "low_freq_list": low_freqs,
    "subduration": 0.03,
    "suboverlap": 0.01,
}
# fix the random seed
np.random.seed(0)

# %%
cot, high_mat, low_mat = cloud_of_tones(
    **sound_properties,
    high_prob=0.7,
    low_prob=0.3,
    )

# %%
storage = {
    "high_tones": high_mat.to_dict(),
    "low_tones": low_mat.to_dict(),
}

# %%
pd.DataFrame(storage["high_tones"])
# %%
from bitarray import bitarray

# create a matrix of 0s and 1s with pandas
matrix = pd.DataFrame(
    {
        "A": [1, 0, 1],
        "B": [0, 1, 0],
        "C": [1, 1, 0],
    }
)

mat = bitarray(matrix.values.flatten().tolist()).to01()

# %%
np.array(bitarray(mat).tolist()).reshape(matrix.shape)
# %%
