"""
Audio Quality Scoring Pipeline (Generator-Agnostic)

This module:
- Generates audio using a generic audio source
- Evaluates quality using loudness, silence, dynamics, spectral balance
- Selects best attempt based on quality score

Total Score: 100
Passing Score: 60
"""

import os
import numpy as np
import librosa
import soundfile as sf

from datetime import datetime
from typing import Dict, Tuple




# =====================================================
# GENERIC AUDIO SOURCE (REPLACEABLE)
# =====================================================

class AudioSourceGenerator:
    """
    Abstract-style audio generator.
    Replace `generate_audio()` with:
    - API-based generator
    - Local ML model
    - Diffusion model
    - Pre-generated audio loader
    """

    def generate_audio(
        self,
        prompt: str,
        duration: int,
        output_path: str,
        **kwargs
    ) -> str:
        """
        MUST return path to a WAV file.
        """

        # 🔁 Example placeholder: load a template sound or silence
        sr = 22050
        audio = np.random.normal(0, 0.05, sr * duration)

        sf.write(output_path, audio, sr)


        return output_path


# =====================================================
# AUDIO QUALITY EVALUATOR
# =====================================================

class AudioQualityEvaluator:
    def __init__(self, pass_score: int = 60):
        self.pass_score = pass_score

    def evaluate(self, audio_path: str, target_duration: float) -> Dict:
        audio, sr = librosa.load(audio_path, mono=True)

        scores = {
            "loudness": self._loudness(audio),
            "duration": self._duration(audio, sr, target_duration),
            "silence": self._silence(audio),
            "dynamics": self._dynamics(audio),
            "spectral": self._spectral(audio, sr),
        }

        total = sum(scores.values())
        scores["total"] = round(total, 2)
        scores["passed"] = total >= self.pass_score

        return scores

    # ---------------- Metrics ----------------

    def _loudness(self, audio: np.ndarray) -> float:
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))

        score = 20
        if peak > 0.98:
            score -= 8
        if rms < 0.04:
            score -= 6
        if rms > 0.6:
            score -= 4

        return max(score, 0)

    def _duration(self, audio: np.ndarray, sr: int, target: float) -> float:
        diff = abs(len(audio) / sr - target)
        if diff <= 1:
            return 15
        elif diff <= 3:
            return 10
        elif diff <= 5:
            return 5
        return 0

    def _silence(self, audio: np.ndarray) -> float:
        energy = audio ** 2
        threshold = np.percentile(energy, 10)
        silent_ratio = np.mean(energy < threshold)

        score = 20
        if silent_ratio > 0.35:
            score -= 12
        elif silent_ratio > 0.25:
            score -= 7
        elif silent_ratio > 0.15:
            score -= 4

        return max(score, 0)

    def _dynamics(self, audio: np.ndarray) -> float:
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        if rms == 0:
            return 0

        crest = peak / rms
        if crest > 8:
            return 20
        elif crest > 5:
            return 14
        elif crest > 3:
            return 8
        return 3

    def _spectral(self, audio: np.ndarray, sr: int) -> float:
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr).mean()
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr).mean()

        score = 25
        if centroid < 400 or centroid > 4000:
            score -= 8
        if rolloff < 2000 or rolloff > 9000:
            score -= 7

        return max(score, 0)


# =====================================================
# QUALITY-CONTROLLED PIPELINE
# =====================================================

class QualityControlledPipeline:
    def __init__(self, min_score: int = 60, max_retries: int = 2):
        self.min_score = min_score
        self.max_retries = max_retries
        self.generator = AudioSourceGenerator()
        self.evaluator = AudioQualityEvaluator(pass_score=min_score)

    def run(
        self,
        prompt: str,
        duration: int,
        output_dir: str
    ) -> Tuple[str, Dict, int]:

        os.makedirs(output_dir, exist_ok=True)

        best_file = None
        best_score = 0
        best_report = None
        attempts = 0

        for i in range(self.max_retries + 1):
            attempts += 1
            filename = f"audio_try_{i}_{datetime.now().strftime('%H%M%S')}.wav"
            path = os.path.join(output_dir, filename)

            audio_path = self.generator.generate_audio(
                prompt=prompt,
                duration=duration,
                output_path=path
            )

            report = self.evaluator.evaluate(audio_path, duration)

            print(f"Attempt {attempts}: {report['total']} / 100")

            if report["total"] > best_score:
                best_score = report["total"]
                best_file = audio_path
                best_report = report

            if report["passed"]:
                return best_file, best_report, attempts

        return best_file, best_report, attempts


# =====================================================
# DEMO RUN
# =====================================================

if __name__ == "__main__":
    pipeline = QualityControlledPipeline(min_score=60, max_retries=2)

    audio_file, score, tries = pipeline.run(
        prompt="ambient electronic background music",
        duration=10,
        output_dir="quality_outputs"
    )

    print("\nFINAL QUALITY REPORT")
    print("-" * 40)
    print("File:", audio_file)
    print("Attempts:", tries)
    for k, v in score.items():
        print(f"{k}: {v}")
