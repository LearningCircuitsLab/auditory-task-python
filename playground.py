# %%
import numpy as np
from sound_functions import cloud_of_tones
# %%


sound_properties = {
    "sample_rate": 48000,
    "duration": 1,
    "ramp_time": 0.005,
    "amplitude": 0.02,
    "high_freq": np.round(np.logspace(np.log10(11000), np.log10(20000), 16)).tolist(),
    "low_freq": np.round(np.logspace(np.log10(5000), np.log10(8000), 16)).tolist(),
    "subduration": 0.03,
    "suboverlap": 0.01,
}


# Generate a cloud of tones
sound, frequencies = cloud_of_tones(**sound_properties, high_perc=95, low_perc=5)

# # print the percentage of high and low tones
print("High tones: ", np.sum(frequencies[1] > 0) / len(frequencies[1]) * 100)
# # print all frequencies different from 0
# h_t = frequencies[1][frequencies[1] > 0]
# print(h_t)
print("Low tones: ", np.sum(frequencies[0] > 0) / len(frequencies[0]) * 100)
# l_t = frequencies[0][frequencies[0] > 0]
# print(l_t)

# plot a spectrogram
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

f, t, Sxx = spectrogram(sound, sound_properties["sample_rate"])
plt.pcolormesh(t, f, 10 * np.log10(Sxx))
plt.ylabel("Frequency [Hz]")
plt.xlabel("Time [sec]")
plt.ylim(0, 20000)  # limit the y axis to 20 kHz
# y axis log
plt.show()

# %%
np.round(np.logspace(np.log10(5000), np.log10(20000), 18)).tolist()[:6]
# %%
# create a sample dataframe
import pandas as pd

sample_df = pd.DataFrame(
    {
        "A": [1, 2, 3, 4, 5],
        "B": [6, 7, 8, 9, 10],
        "C": [11, 12, 13, 14, 15],
    }
)
sample_df

# %%
sample_df.to_dict(orient="records")
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
