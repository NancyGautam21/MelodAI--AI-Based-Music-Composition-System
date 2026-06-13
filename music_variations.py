from backend.music_generator import generate_music_pipeline

def generate_variations(base_prompt, num_variations=3, duration=30):
    """
    Generate multiple variations of the same prompt.
    """
    files = []
    for i in range(num_variations):
        variation_prompt = f"{base_prompt} (variation {i+1})"
        audio_file, params, _ = generate_music_pipeline(variation_prompt, duration)
        files.append(audio_file)
    return files

def extend_music(base_prompt, extension_duration=30):
    """
    Extend the existing music.
    """
    new_prompt = f"{base_prompt} (extended +{extension_duration}s)"
    audio_file, params, _ = generate_music_pipeline(new_prompt, duration=extension_duration)
    return audio_file