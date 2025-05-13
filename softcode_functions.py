from village.devices.sound_device import sound_device
from village.settings import settings
from sound_functions import tone_generator
import numpy as np
from village.manager import get_task

task = get_task()

def function1():
    # stop sound
    sound_device.stop()


def function2():
    # load the sound loaded in manager
    sound_device.load(right=task.twoAFC_sound, left=task.twoAFC_sound)


def function3():
    # play the sound
    sound_device.play()


def function10():
    # create a loud noise
    duration = 5
    ramptime = 0.05
    amplitude = 0.05
    sample_rate = settings.get("SAMPLERATE")
    frequency = 10000
    # get the time steps
    # Create time array
    total_time_steps = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    scary_sound = tone_generator(total_time_steps, ramptime, amplitude, frequency)
    # load the sound loaded in manager
    sound_device.load(right=scary_sound, left=scary_sound)
    # play the sound
    sound_device.play()


def function9():
    # create a loud noise
    duration = 5
    ramptime = 0.05
    amplitude = 0.05
    sample_rate = settings.get("SAMPLERATE")
    frequency = 5000
    # get the time steps
    # Create time array
    total_time_steps = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    scary_sound = tone_generator(total_time_steps, ramptime, amplitude, frequency)
    # load the sound loaded in manager
    sound_device.load(right=scary_sound, left=scary_sound)
    # play the sound
    sound_device.play()


def function8():
    # create a loud noise
    duration = 5
    ramptime = 0.05
    amplitude = 0.05
    sample_rate = settings.get("SAMPLERATE")
    frequency = 1000
    # get the time steps
    # Create time array
    total_time_steps = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    scary_sound = tone_generator(total_time_steps, ramptime, amplitude, frequency)
    # load the sound loaded in manager
    sound_device.load(right=scary_sound, left=scary_sound)
    # play the sound
    sound_device.play()


def function11():
    # create a loud noise
    duration = 5
    ramptime = 0.05
    amplitude = 0.05
    sample_rate = settings.get("SAMPLERATE")
    frequency = 20000
    # get the time steps
    # Create time array
    total_time_steps = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    scary_sound = tone_generator(total_time_steps, ramptime, amplitude, frequency)
    # load the sound loaded in manager
    sound_device.load(right=scary_sound, left=scary_sound)
    # play the sound
    sound_device.play()


def function12():
    # create a loud noise
    duration = 5
    ramptime = 0.05
    amplitude = 0.05
    sample_rate = settings.get("SAMPLERATE")
    frequency = 40000
    # get the time steps
    # Create time array
    total_time_steps = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    scary_sound = tone_generator(total_time_steps, ramptime, amplitude, frequency)
    # load the sound loaded in manager
    sound_device.load(right=scary_sound, left=scary_sound)
    # play the sound
    sound_device.play()


