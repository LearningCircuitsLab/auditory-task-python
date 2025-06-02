from village.devices.sound_device import sound_device
from village.settings import settings
import numpy as np
import time

duration = 0.5
fs = float(settings.get("SAMPLERATE"))
span = 1000
end = 40001
start = span
amp = 0.05
# amp = {
#     5000: 0.1,
#     10000: 0.138,
#     15000: 0.294,
#     20000: 0.385,
#     25000: 0.5,
#     30000: 0.33,
#     35000: 0.625,
#     40000: 1.0,
# }

frequencies = np.arange(start, end, span)

t = np.linspace(0, duration, int(fs * duration), endpoint=False)

signal = np.zeros_like(t)

for f in frequencies:
    signal = amp*np.sin(2 * np.pi * f * t)
    sound_device.load(right=signal, left=signal)
    sound_device.play()
    time.sleep(duration + 0.05)  # Wait for the sound to finish playing
    sound_device.stop()

#signal /= len(frequencies)
#signal += amp*np.sin(2 * np.pi * f * t)

#sound_device.load(right=signal, left=signal)
#sound_device.play()
#time.sleep(duration + 0.5)  # Wait for the sound to finish playing