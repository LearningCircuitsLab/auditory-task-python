from village.devices.sound_device import sound_device
from village.manager import manager


def function2():
    # load the sound loaded in manager
    sound_device.load(right=manager.twoAFC_sound, left=None)


def function3():
    # play the sound
    sound_device.play()
