


"""
Multi-Model Manager for Text-to-Music Generation
Uses MusicLDM via HuggingFace Diffusers
(NO audiocraft, NO stable-audio-tools)
"""

import time
import torch
import numpy as np
from typing import Dict, Optional, Tuple, List
from diffusers import MusicLDMPipeline
import warnings
warnings.filterwarnings("ignore")


# --------------------------------------------------
# DEVICE UTILITY
# --------------------------------------------------
def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


# --------------------------------------------------
# MUSICLDM MODEL WRAPPER
# --------------------------------------------------
class MusicLDMModel:
    def __init__(self, model_id: str):
        self.device = get_device()
        self.model_id = model_id

        self.pipe = MusicLDMPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )

        self.pipe = self.pipe.to(self.device)

    def generate(
        self,
        prompt: str,
        duration: int,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 200
    ):
        audio_length = duration * 1024  # MusicLDM internal scale

        with torch.no_grad():
            output = self.pipe(
                prompt,
                audio_length_in_s=duration,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps
            )

        return output.audios[0]


# --------------------------------------------------
# MODEL MANAGER
# --------------------------------------------------
class ModelManager:
    """
    Multi-model manager using MusicLDM
    """

    def __init__(self):
        self.models: Dict[str, MusicLDMModel] = {}
        self.current_model: Optional[MusicLDMModel] = None
        self.current_model_name: Optional[str] = None

        self.model_info = {
            "musicldm-small": {
                "hf_id": "cvssp/musicldm-small",
                "params": "400M",
                "speed": "Fast",
                "quality": "Good",
                "max_duration": 90
            },
            "musicldm-base": {
                "hf_id": "cvssp/musicldm",
                "params": "1B",
                "speed": "Balanced",
                "quality": "Very Good",
                "max_duration": 60
            }
        }

        print("🎶 MusicLDM ModelManager initialized")
        print(f"📦 Available models: {list(self.model_info.keys())}")

    # --------------------------------------------------
    # MODEL SELECTION
    # --------------------------------------------------
    def select_optimal_model(
        self,
        duration: int,
        quality_preference: str = "balanced",
        user_model: Optional[str] = None
    ) -> str:

        if user_model and user_model in self.model_info:
            return user_model

        if quality_preference == "fast" or duration > 45:
            return "musicldm-small"
        return "musicldm-base"

    # --------------------------------------------------
    # LOAD / UNLOAD
    # --------------------------------------------------
    def load_model(self, model_name: str) -> bool:
        if model_name in self.models:
            self.current_model = self.models[model_name]
            self.current_model_name = model_name
            return True

        if model_name not in self.model_info:
            print(f"❌ Unknown model: {model_name}")
            return False

        try:
            hf_id = self.model_info[model_name]["hf_id"]
            print(f"📥 Loading {model_name} ({hf_id})")

            model = MusicLDMModel(hf_id)

            self.models[model_name] = model
            self.current_model = model
            self.current_model_name = model_name

            print(f"✅ Loaded {model_name}")
            return True
        except Exception as e:
            print(f"❌ Load failed: {e}")
            return False

    def unload_model(self, model_name: str):
        if model_name in self.models:
            del self.models[model_name]

            if self.current_model_name == model_name:
                self.current_model = None
                self.current_model_name = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            print(f"🗑️ Unloaded {model_name}")

    # --------------------------------------------------
    # GENERATION
    # --------------------------------------------------
    def generate(
        self,
        prompt: str,
        duration: int,
        model_name: Optional[str] = None,
        guidance_scale: float = 3.5,
        steps: int = 200
    ) -> Tuple[Optional[np.ndarray], Dict]:

        if model_name:
            if not self.load_model(model_name):
                return None, {"error": "Model load failed"}
        elif not self.current_model:
            auto = self.select_optimal_model(duration)
            if not self.load_model(auto):
                return None, {"error": "Auto model load failed"}

        try:
            print(f"🎵 Generating with {self.current_model_name}")
            start = time.time()

            audio = self.current_model.generate(
                prompt=prompt,
                duration=duration,
                guidance_scale=guidance_scale,
                num_inference_steps=steps
            )

            gen_time = time.time() - start

            return audio, {
                "model": self.current_model_name,
                "generation_time": gen_time,
                "prompt": prompt,
                "duration": duration
            }

        except Exception as e:
            return None, {"error": str(e)}

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------
    def get_fallback_model(self, failed_model: str) -> Optional[str]:
        return "musicldm-small" if failed_model != "musicldm-small" else None

    def generate_with_fallback(
        self,
        prompt: str,
        duration: int,
        preferred_model: str,
        **kwargs
    ) -> Tuple[Optional[np.ndarray], Dict]:

        current = preferred_model
        attempts = []

        while current:
            audio, meta = self.generate(
                prompt=prompt,
                duration=duration,
                model_name=current,
                **kwargs
            )

            attempts.append({
                "model": current,
                "success": audio is not None
            })

            if audio is not None:
                meta["attempts"] = attempts
                meta["final_model"] = current
                return audio, meta

            current = self.get_fallback_model(current)

        return None, {"error": "All models failed", "attempts": attempts}

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------
    def cleanup(self):
        print("🧹 Cleaning up models...")
        for m in list(self.models.keys()):
            self.unload_model(m)
        self.models.clear()
        print("✅ Cleanup complete")


# --------------------------------------------------
# GLOBAL INSTANCE
# --------------------------------------------------
model_manager = ModelManager()


def get_model_manager() -> ModelManager:
    return model_manager


# --------------------------------------------------
# TEST
# --------------------------------------------------
if __name__ == "__main__":
    manager = ModelManager()

    audio, meta = manager.generate_with_fallback(
        prompt="ambient cinematic music with soft strings and pads",
        duration=15,
        preferred_model="musicldm-base"
    )

    print("\n📊 Metadata:")
    print(meta)
