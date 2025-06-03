
"""
# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from sound_functions import generate_tone_matrix, cloud_of_tones_matrices, sound_matrix_to_sound

# %%
lowest_freq = 5000
highest_freq = 40000
freqs_log_spaced = np.round(np.logspace(np.log10(lowest_freq), np.log10(highest_freq), 18)).tolist()
low_freqs = freqs_log_spaced[:6]
high_freqs = freqs_log_spaced[-6:]
# Define sound properties
sound_properties_for_cot_mat = {
    "duration": .5,
    "high_amplitude_mean": 70,
    "low_amplitude_mean": 70,
    "amplitude_std": 2,
    "high_freq_list": high_freqs,
    "low_freq_list": low_freqs,
    "subduration": 0.03,
    "suboverlap": 0.01,
    "ambiguous_beginning_time": 0.05,
}
sound_properties_for_sound_making = {
    "sample_rate": 192000,
    "ramp_time": 0.005,
    "subduration": 0.03,
    "suboverlap": 0.01,
}
# fix the random seed
np.random.seed(0)


# %%
# Generate the two component matrices for the cloud of tones
high_mat, low_mat = cloud_of_tones_matrices(
    **sound_properties_for_cot_mat,
    high_prob=.7,
    low_prob=.3)

from village.manager import manager

print(manager.sound_calibration.get_sound_gain(0, 74.7, "one_thousand_hz_calibration"))

# Replace 'self' with an appropriate object or variable, e.g., 'calibration_tool'
high_mat_calibrated = high_mat.map(
    lambda db: manager.sound_calibration.get_sound_gain(
        0,
        db,
        "one_thousand_hz_calibration",
    )
)

low_mat_calibrated = low_mat.map(
    lambda db: manager.sound_calibration.get_sound_gain(
        0,
        db,
        "one_thousand_hz_calibration",
    )
)


# plot a heatmap of the cloud of tones
# Create a custom colormap that is white when the value is 0
colors = [(1, 1, 1), (0.2, 0.6, 0.2)]  # White to seagreen
n_bins = 100  # Discretize the interpolation into bins
cmap_name = 'white_to_seagreen'
cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
plt.figure(figsize=(10, 3))
mat_to_plot = pd.concat([high_mat_calibrated[::-1], low_mat_calibrated[::-1]])
sns.heatmap(mat_to_plot,
            cmap=cmap,
            cbar_kws={'label': 'Amplitude (dB)'})
plt.hlines(6, 0, high_mat.shape[1], colors='gray', linestyles='dashed')
plt.xlabel("Time (ms)")
plt.ylabel("Frequency (Hz)")
plt.title("Cloud of Tones")
plt.show()

"""