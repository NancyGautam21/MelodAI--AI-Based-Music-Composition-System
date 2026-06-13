import os
import librosa
import soundfile as sf
import numpy as np

class AudioProcessor:
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate

    def load_audio(self, path):
        y, sr = librosa.load(path, sr=self.sr)
        return y, sr

    def save_audio(self, y, path):
        sf.write(path, y, self.sr)

    def normalize(self, y):
        return librosa.util.normalize(y)

    def apply_eq(self, y, preset):
        if preset == "studio":
            y = librosa.effects.preemphasis(y)
        elif preset == "concert":
            y = y * 1.1
        elif preset == "bedroom":
            y = y * 0.95
        return y

    def enhance(self, input_path, preset="studio"):
        y, _ = self.load_audio(input_path)
        y = self.normalize(y)
        y = self.apply_eq(y, preset)

        os.makedirs("output/enhanced", exist_ok=True)
        output_path = f"output/enhanced/enhanced_{preset}.wav"
        self.save_audio(y, output_path)

        return output_path
