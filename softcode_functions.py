
import os
import pickle

from village.devices.sound_device import SoundDevice, sound_device


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

if __name__ == "__main__":
    sd = SoundDevice(samplerate=48000)
    sound = pickle.load(open(TEMP_SOUND_PATH, "rb"))
    sd.load(sound)
    sd.play()
    import time
    time.sleep(1)