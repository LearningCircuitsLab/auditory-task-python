# %%
import numpy as np

from sound_functions import cloud_of_tones

# %%

# Define frequencies
lowest_freq = 5000
highest_freq = 20000
freqs_log_spaced = np.round(np.logspace(np.log10(lowest_freq), np.log10(highest_freq), 18)).tolist()
low_freq_list = freqs_log_spaced[:6]
high_freq_list = freqs_log_spaced[-6:]
# Define sound properties
sound_properties = {
    "sample_rate": 48000,
    "duration": 1,
    "ramp_time": 0.005,
    "high_amplitude_mean": 70,
    "low_amplitude_mean": 60,
    "amplitude_std": 2,
    "high_freq_list": high_freq_list,
    "low_freq_list": low_freq_list,
    "subduration": 0.03,
    "suboverlap": 0.01,
}

# Generate a cloud of tones
cot, _, _ = cloud_of_tones(**sound_properties, high_prob=.7, low_prob=.3)
print(cot.shape)

# %%
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
