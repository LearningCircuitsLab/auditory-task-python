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


# %%
import pandas as pd
import numpy as np

def generate_tone_matrix(frequencies, n_timebins, total_probability):
    """
    Generate a matrix of tones across time bins and frequencies.
    Each frequency has an independent probability in each time bin.
    
    Parameters:
    frequencies (list): List of frequencies to consider
    n_timebins (int): Number of time bins
    total_probability (float): Probability of at least one tone in each time bin (0-1)
    
    Returns:
    pd.DataFrame: Matrix where rows are frequencies and columns are time bins
    """
    if not 0 <= total_probability <= 1:
        raise ValueError("Total probability must be between 0 and 1")
    
    # Calculate individual probability for each frequency
    # Using the formula: 1 - (1-p)^n = total_probability
    # where p is individual probability and n is number of frequencies
    # Solving for p: p = 1 - (1-total_probability)^(1/n)
    n_frequencies = len(frequencies)
    individual_probability = 1 - (1 - total_probability) ** (1 / n_frequencies)
    
    # Generate matrix using independent Bernoulli trials
    matrix = np.random.random((len(frequencies), n_timebins)) < individual_probability
    
    # Convert to integer type (0s and 1s)
    matrix = matrix.astype(int)
    
    # Create DataFrame with proper labels
    df = pd.DataFrame(matrix, 
                     index=frequencies,
                     columns=[f'time_{t}' for t in range(n_timebins)])
    
    return df, individual_probability

# Function to verify probabilities
def verify_probabilities(matrix, individual_prob, total_prob):
    """
    Verify the probabilities in the generated matrix
    """
    # Calculate actual probability of at least one tone per time bin
    actual_total_prob = np.mean(matrix.sum(axis=0) > 0)
    
    # Calculate actual individual probability per frequency
    actual_individual_prob = np.mean(matrix)
    
    return {
        'expected_total_prob': total_prob,
        'actual_total_prob': actual_total_prob,
        'expected_individual_prob': individual_prob,
        'actual_individual_prob': actual_individual_prob
    }

# Example usage function
def example_usage():
    # Example parameters
    freqs = [440, 880, 1760, 3520, 7040]  # A4 to A7
    n_bins = 1000  # Large number for better probability verification
    total_prob = 0.9
    
    # Generate matrix
    result, ind_prob = generate_tone_matrix(freqs, n_bins, total_prob)
    
    # Verify probabilities
    stats = verify_probabilities(result, ind_prob, total_prob)

    # add amplitude values to the matrix
    result_amp = add_amplitude_to_sound_matrix(result, 60, 2)
    
    return result, stats, result_amp

# Let's modulate now the amplitude of the tones,
# and add that value to the entries of the matrix

def add_amplitude_to_sound_matrix(matrix, amplitude_mean, amplitude_std):
    """
    Add amplitude values to a matrix of sounds.
    
    Parameters:
    matrix (pd.DataFrame): Matrix of sounds
    amplitude_mean (float): Mean amplitude value
    amplitude_std (float): Standard deviation of amplitude values
    
    Returns:
    pd.DataFrame: Matrix with amplitude values added
    """
    # Generate amplitudes
    amplitudes = np.random.normal(amplitude_mean, amplitude_std, matrix.shape)
    
    # Substitute amplitudes into matrix where matrix entries are 1
    matrix = matrix * amplitudes
    
    return matrix

# %%
r, s, r_amp = example_usage()
# %%
