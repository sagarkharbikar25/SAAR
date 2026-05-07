import sounddevice as sd
import numpy as np

class MicLevel:
    def __init__(self):
        self.level = 0.0

    def callback(self, indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        self.level = min(volume_norm, 1.0)

    def start(self):
        self.stream = sd.InputStream(
            callback=self.callback,
            channels=1,
            samplerate=16000
        )
        self.stream.start()

    def get_level(self):
        return self.level
