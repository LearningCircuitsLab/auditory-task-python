from village.devices.sound_device import sound_device
from village.settings import settings
import numpy as np
import time
import pandas as pd



duration = 0.2
fs = float(settings.get("SAMPLERATE"))
span = 1000
end = 40001
start = span
amp = 0.05


frequencies = np.arange(start, end, span)

t = np.linspace(0, duration, int(fs * duration), endpoint=False)

signal = np.zeros_like(t)

for f in frequencies:
    signal = amp*np.sin(2 * np.pi * f * t)
    sound_device.load(right=signal, left=signal)
    sound_device.play()
    time.sleep(duration+0.1)  # Wait for the sound to finish playing
    sound_device.stop()


#signal /= len(frequencies)
#signal += amp*np.sin(2 * np.pi * f * t)

#sound_device.load(right=signal, left=signal)
#sound_device.play()
#time.sleep(duration + 0.5)  # Wait for the sound to finish playing