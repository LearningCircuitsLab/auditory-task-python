import numpy as np
import pandas as pd


def tone_generator(time, ramp_time, amplitude, frequency):
    """
    Generate a single tone with ramping

    Args:
        time (np.ndarray): Time array
        ramp_time (float): Ramp up/down time
        amplitude (float): Tone amplitude
        frequency (float): Tone frequency

    Returns:
        np.ndarray: Generated tone
    """
    # If no frequency specified, return zero array
    if frequency == 0:
        return np.zeros_like(time)

    # Generate tone
    tone = amplitude * np.sin(2 * np.pi * frequency * time)

    # Calculate ramp points
    sample_rate = 1 / (time[1] - time[0])
    ramp_points = int(ramp_time * sample_rate)

    # Create ramp arrays
    if ramp_points > 0:
        ramp_up = np.linspace(0, 1, ramp_points)
        ramp_down = np.linspace(1, 0, ramp_points)

        # Apply ramps
        tone[:ramp_points] *= ramp_up
        tone[-ramp_points:] *= ramp_down

    return tone


def generate_tones_deprecated(
    no_of_tones_to_gen,
    sample_rate,
    duration,
    ramp_time,
    amplitude,
    high_freq,
    low_freq,
    high_perc,
    low_perc,
):
    """
    Generate tones with specified characteristics

    Args:
        no_of_tones_to_gen (int): Number of tones to generate
        sample_rate (int): Sampling rate in Hz
        duration (float): Duration of each tone
        ramp_time (float): Ramp up/down time
        amplitude (float): Base amplitude
        high_freq (array-like): High frequency range
        low_freq (array-like): Low frequency range
        high_perc (float): Probability of high tone
        low_perc (float): Probability of low tone

    Returns:
        np.ndarray: Generated tones
        np.ndarray: Picked frequencies
    """
    # Create time array
    time = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Generate empty matrix to contain sounds
    tones = np.zeros((no_of_tones_to_gen, len(time)))

    # create empty array of nans
    picked_frequencies = np.empty((2, no_of_tones_to_gen))
    picked_frequencies[:] = np.nan

    for i in range(no_of_tones_to_gen):
        # Default amplitude modulator
        amplitude_modulator = 1

        # Determine frequencies to generate
        h_freq = 0
        l_freq = 0

        # Random picks for high and low frequencies
        pick_h = np.random.randint(1, 101)
        pick_l = np.random.randint(1, 101)

        # Flags to check if both sounds are combined
        h_flag = False
        l_flag = False

        # Select high frequency
        if pick_h <= high_perc:
            h_freq = np.random.choice(high_freq)
            h_flag = True

        # Select low frequency
        if pick_l <= low_perc:
            l_freq = np.random.choice(low_freq)
            l_flag = True

        # Adjust amplitude if both tones are played
        # TODO: This is wrong!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
        if h_flag and l_flag:
            amplitude_modulator = 2

        # Generate high and low tones
        high_tone = tone_generator(
            time, ramp_time, amplitude / amplitude_modulator, h_freq
        )
        low_tone = tone_generator(
            time, ramp_time, amplitude / amplitude_modulator, l_freq
        )

        # Combine tones
        tones[i, :] = high_tone + low_tone

        # Save the picked frequencies
        picked_frequencies[0, i] = l_freq
        picked_frequencies[1, i] = h_freq

    return tones, picked_frequencies


def cloud_of_tones_deprecated(
    sample_rate,
    duration,
    ramp_time,
    amplitude,
    high_freq,
    low_freq,
    high_perc,
    low_perc,
    subduration,
    suboverlap,
):
    """
    Generate a cloud of overlapping tones

    Args:
        sample_rate (int): Sample rate in Hz
        duration (float): Total duration of sound
        ramp_time (float): Ramp up/down time
        amplitude (float): Median amplitude
        high_freq (array-like): High frequency range
        low_freq (array-like): Low frequency range
        high_perc (float): Probability of high tone
        low_perc (float): Probability of low tone
        subduration (float): Duration of each tone
        suboverlap (float): Overlap between consecutive tones

    Returns:
        np.ndarray: Generated sound array
        np.ndarray: Frequencies of generated tones
    """
    # Validate inputs
    non_overlap = subduration - suboverlap
    if non_overlap <= 0:
        raise ValueError("Tones overlap is bigger than the duration")

    no_of_tones_to_gen = int(np.floor(duration / non_overlap))
    if no_of_tones_to_gen < 1:
        raise ValueError(
            "Duration and subduration/suboverlap ratio might not make sense"
        )

    # Generate tones
    tones, frequencies = generate_tones_deprecated(
        no_of_tones_to_gen,
        sample_rate,
        subduration,
        ramp_time,
        amplitude,
        high_freq,
        low_freq,
        high_perc,
        low_perc,
    )

    # Prepare output sound array
    sound_length = int(sample_rate * duration)
    tone_length = int(sample_rate * subduration)
    sound = np.zeros(sound_length + tone_length)  # Add tail to avoid failures

    # Calculate space between tone placements
    space_length = int(sample_rate * non_overlap)
    idx = np.arange(0, sound_length, space_length)

    # Concatenate tones
    for i in range(tones.shape[0]):
        sound[idx[i] : idx[i] + tone_length] += tones[i, :]

    # Clip the tail
    sound = sound[:sound_length]

    # Add background white noise over the entire sound with 5% of the amplitude
    noise = np.random.normal(0, amplitude * .05, sound_length)
    sound += noise

    return sound, frequencies


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


def cloud_of_tones(
    sample_rate: int,
    duration: float,
    high_freq_list: list,
    low_freq_list: list,
    high_prob: float,
    low_prob: float,
    high_amplitude_mean: float,
    low_amplitude_mean: float,
    amplitude_std: float,
    subduration: float,
    suboverlap: float,
    ramp_time: float,
):
    """
    Generate a cloud of overlapping tones

    Args:
        sample_rate (int): Sample rate in Hz
        duration (float): Total duration of sound in seconds
        high_freq_list (array-like): High frequency range (Hz)
        low_freq_list (array-like): Low frequency range (Hz)
        high_prob (float): Probability of high tone
        low_prob (float): Probability of low tone
        high_amplitude_mean (float): Mean amplitude for high tones in dB
        low_amplitude_mean (float): Mean amplitude for low tones in dB
        amplitude_std (float): Standard deviation of amplitude values in dB
        subduration (float): Duration of each tone in seconds
        suboverlap (float): Overlap between consecutive tones in seconds
        ramp_time (float): Ramp up/down time in seconds

    Returns:
        np.ndarray: Generated sound array
        pd.DataFrame: High tones sound matrix (frequencies x timebins) with amplitude values
        pd.DataFrame: Low tones sound matrix (frequencies x timebins) with amplitude values
    """
    # Validate inputs
    non_overlap = subduration - suboverlap
    if non_overlap <= 0:
        raise ValueError("Tones overlap is bigger than the duration")

    number_of_timebins = int(np.floor(duration / non_overlap))
    if number_of_timebins < 1:
        raise ValueError(
            "Duration and subduration/suboverlap ratio might not make sense"
        )
    
    # Generate high and low tone matrices
    high_tones_mat, _ = generate_tone_matrix(
        high_freq_list, number_of_timebins, high_prob
    )
    high_sound_mat = add_amplitude_to_sound_matrix(
        high_tones_mat, high_amplitude_mean, amplitude_std
    )
    low_tones_mat, _ = generate_tone_matrix(
        low_freq_list, number_of_timebins, low_prob
    )
    low_sound_mat = add_amplitude_to_sound_matrix(
        low_tones_mat, low_amplitude_mean, amplitude_std
    )

    # Generate a sound array for each frequency
    freqs_sounds = pd.concat([high_sound_mat, low_sound_mat]).apply(
        generate_frequency_sound,
        axis=1,
        args=(
            sample_rate,
            subduration,
            suboverlap,
            ramp_time,
        )
    )

    cot = np.sum(freqs_sounds.values, axis=0)
    

    return cot, high_sound_mat, low_sound_mat


def generate_frequency_sound(row, sample_rate, subduration, suboverlap, ramp_time):
    """
    Generate a sound array for a given frequency

    Args:
        row (pd.Series): Row of a DataFrame with time bins as index
        sample_rate (int): Sample rate in Hz
        subduration (float): Duration of each tone in seconds
        suboverlap (float): Overlap between consecutive tones in seconds
        ramp_time (float): Ramp up/down time in seconds

    Returns:
        np.ndarray: Generated sound array
    """
    # Total duration of sound in seconds
    total_duration = len(row) * (subduration - suboverlap)
    # Create time array
    total_time_steps = np.linspace(0, total_duration, int(sample_rate * total_duration), endpoint=False)
    # Generate empty array to contain sounds
    sound = np.zeros(len(total_time_steps))

    # Calculate space between tone placements
    tone_length = int(sample_rate * subduration)
    space_length = int(sample_rate * (subduration - suboverlap))
    idx = np.arange(0, len(total_time_steps), space_length)

    # Generate tones and concatenate them
    for i in range(len(row)):
        if row.iloc[i] > 0:
            # TODO: convert decibels to amplitude
            amplitude = 0.05
            sound[idx[i] : idx[i] + tone_length] += tone_generator(
                total_time_steps[idx[i] : idx[i] + tone_length],
                ramp_time,
                amplitude,
                row.name,
            )
    
    return sound

if __name__ == "__main__":
    # # Define frequencies
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

    # # Generate a cloud of tones
    # cot, _, _ = cloud_of_tones(**sound_properties, high_prob=.7, low_prob=.3)
    # print(cot.shape)

    # # play it
    import time

    from village.devices.sound_device import SoundDevice

    sd = SoundDevice(sound_properties["sample_rate"])

    import pickle

    from softcode_functions import TEMP_SOUND_PATH

    cot = pickle.load(open(TEMP_SOUND_PATH, "rb"))

    sd.load(cot)
    sd.play()
    # time.sleep(2)

    # # # print the percentage of high and low tones
    # print("High tones: ", np.sum(frequencies[1] > 0) / len(frequencies[1]) * 100)
    # # # print all frequencies different from 0
    # # h_t = frequencies[1][frequencies[1] > 0]
    # # print(h_t)
    # print("Low tones: ", np.sum(frequencies[0] > 0) / len(frequencies[0]) * 100)
    # # l_t = frequencies[0][frequencies[0] > 0]
    # # print(l_t)

    # plot a spectrogram

    import matplotlib.pyplot as plt
    from scipy.signal import spectrogram



    f, t, Sxx = spectrogram(cot, sound_properties["sample_rate"])
    plt.pcolormesh(t, f, 10 * np.log10(Sxx))
    plt.ylabel("Frequency [Hz]")
    plt.xlabel("Time [sec]")
    plt.ylim(0, 20000)  # limit the y axis to 20 kHz
    # y axis log
    plt.show()
