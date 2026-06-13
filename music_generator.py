import os
from scipy.io.wavfile import write
import numpy as np
import time

os.makedirs("outputs", exist_ok=True)

def generate_music_pipeline(prompt, duration=5, temperature=1.0, model="small"):
    """
    Generates a test sine wave audio file to simulate music generation.
    """
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate*duration), False)
    
    # Generate a sine wave with frequency based on prompt hash
    freq = 220 + (hash(prompt) % 880)  # 220Hz to 1100Hz
    audio = 0.5 * np.sin(2 * np.pi * freq * t)
    
    # Convert to 16-bit PCM
    audio_int16 = np.int16(audio * 32767)
    
    filename = f"outputs/{prompt[:10].replace(' ','')}{int(time.time())}.wav"
    write(filename, sample_rate, audio_int16)
    
    params = {
        "duration": duration,
        "temperature": temperature,
        "model": model
    }
    
    return filename, params, prompt