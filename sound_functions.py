import numpy as np


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


def generate_tones(
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


def cloud_of_tones(
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
    tones, frequencies = generate_tones(
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

if __name__ == "__main__":
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

    from village.devices.sound_device import SoundDevice

    sd = SoundDevice(samplerate=sound_properties["sample_rate"])
    sd.load(sound)
    sd.play()

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
