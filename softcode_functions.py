
import os
import pickle
from village.devices.sound_device import sound_device

def function2():
    # find the sound
    sound = pickle.load(open(TEMP_SOUND_PATH, "rb"))
    # load the sound
    sound_device.load(sound)


def function3():
    # play the sound
    sound_device.play()


# Name of a temporary file to store the sound during the task
TEMP_SOUND_PATH = os.path.join(os.path.dirname(__file__), "temp_sound.pkl")