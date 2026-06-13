from streamlit_lottie import st_lottie
import requests
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import time
import csv
import librosa
import librosa.display

from backend.music_generator import generate_music_pipeline
from backend.music_variations import generate_variations, extend_music
from frontend.example_prompts import EXAMPLES
from utils.helpers import generate_unique_id, current_timestamp


import base64

def set_glass_glow_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        /* ===== FULL APP BACKGROUND ===== */
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* ===== FROSTED GLASS OVERLAY ===== */
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(255, 255, 255, 0.25);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            z-index: -1;
        }}

        /* ===== GLASS CONTAINER ===== */
        .block-container {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 2rem;
            box-shadow:
                0 0 40px rgba(147, 51, 234, 0.25),
                0 0 80px rgba(236, 72, 153, 0.18);
            animation: glassGlow 8s ease-in-out infinite;
        }}

        @keyframes glassGlow {{
            0% {{
                box-shadow:
                    0 0 40px rgba(147, 51, 234, 0.2),
                    0 0 80px rgba(236, 72, 153, 0.15);
            }}
            50% {{
                box-shadow:
                    0 0 70px rgba(147, 51, 234, 0.35),
                    0 0 120px rgba(236, 72, 153, 0.25);
            }}
            100% {{
                box-shadow:
                    0 0 40px rgba(147, 51, 234, 0.2),
                    0 0 80px rgba(236, 72, 153, 0.15);
            }}
        }}

        /* ===== BLACK FONT THEME ===== */
        html, body, p, span, label, div {{
            color: #111827;
        }}

        h1, h2, h3 {{
            color: #030712;
            text-shadow: 0 1px 2px rgba(255,255,255,0.6);
        }}

        /* ===== INPUTS ===== */
        textarea, input, select {{
            background: rgba(255,255,255,0.85) !important;
            color: #030712 !important;
            border-radius: 12px;
            border: 1px solid rgba(0,0,0,0.15);
        }}

        /* ===== SIDEBAR GLASS ===== */
        [data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.35);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid rgba(0,0,0,0.1);
        }}

        [data-testid="stSidebar"] * {{
            color: #111827;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# APPLY GLASS GLOW BACKGROUND
set_glass_glow_background("assets/background.jpg.jpeg")






def add_floating_music_icons():
    st.markdown(
        """
        <style>
        /* ===== FLOATING MUSIC ICONS (DARK BLACK) ===== */
        .music-float-container {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 1;
            overflow: hidden;
        }

        .music-icon {
            position: absolute;
            font-size: 34px;
            color: rgba(0, 0, 0, 0.75); /* DARK BLACK */
            text-shadow:
                0 2px 4px rgba(255,255,255,0.4); /* glass contrast */
            animation: floatMusic linear infinite;
        }

        .music-icon:nth-child(1) { left: 6%;  animation-duration: 22s; animation-delay: 0s; }
        .music-icon:nth-child(2) { left: 20%; animation-duration: 28s; animation-delay: 2s; }
        .music-icon:nth-child(3) { left: 36%; animation-duration: 24s; animation-delay: 4s; }
        .music-icon:nth-child(4) { left: 52%; animation-duration: 32s; animation-delay: 1s; }
        .music-icon:nth-child(5) { left: 70%; animation-duration: 26s; animation-delay: 3s; }
        .music-icon:nth-child(6) { left: 86%; animation-duration: 34s; animation-delay: 5s; }

        @keyframes floatMusic {
            0% {
                transform: translateY(110vh) rotate(0deg);
            }
            100% {
                transform: translateY(-20vh) rotate(360deg);
            }
        }
        </style>

        <div class="music-float-container">
            <div class="music-icon">🎵</div>
            <div class="music-icon">🎶</div>
            <div class="music-icon">🎧</div>
            <div class="music-icon">🎼</div>
            <div class="music-icon">🎹</div>
            <div class="music-icon">🎤</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# APPLY FLOATING ICONS
add_floating_music_icons()


# ================================
# HERO CONTENT (WRAPS YOUR HEADER)
# ================================
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-glass">
        <div class="hero-title">MelodAI</div>
        <div class="hero-subtitle">AI-Powered Music Generator</div>
        <div class="hero-desc">
            Create studio-quality music by describing mood, style, and context.
            Powered by advanced generative AI.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)




# ===== CACHE MANAGER =====
class CacheManager:
    def __init__(self):
        if "cache" not in st.session_state:
            st.session_state.cache = {}

    def make_key(self, prompt, duration, temperature, model):
        return f"{prompt}_{duration}_{temperature}_{model}"

    def get(self, key):
        return st.session_state.cache.get(key)

    def set(self, key, value):
        st.session_state.cache[key] = value


# Initialize cache manager
Cache_Manager = CacheManager()


# ===== TASK 3.6: Performance & UX polish =====
st.set_page_config(
    page_title="MelodAI",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>

/* =====================
   GLOBAL FONT SYSTEM
===================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #0f172a;
}

/* =====================
   TITLES & HEADINGS
===================== */
h1 {
    font-weight: 900;
    letter-spacing: -1px;
}

h2, h3 {
    font-weight: 700;
}

/* =====================
   HERO TEXT
===================== */
.hero-title {
    font-weight: 900;
    letter-spacing: -1.2px;
}

.hero-subtitle {
    font-weight: 600;
}

/* =====================
   SIDEBAR TEXT
===================== */
section[data-testid="stSidebar"] * {
    font-size: 14px;
    font-weight: 500;
    color: #020617;
}

/* =====================
   INPUTS (TEXT, SLIDER)
===================== */
input, textarea, select {
    background: rgba(255,255,255,0.55) !important;
    backdrop-filter: blur(14px);
    border-radius: 14px !important;
    border: 1px solid rgba(0,0,0,0.15) !important;
    color: #020617 !important;
}

/* =====================
   BUTTONS
===================== */
button[kind="primary"] {
    background: linear-gradient(135deg, #020617, #111827) !important;
    color: white !important;
    border-radius: 18px !important;
    padding: 12px 22px !important;
    font-weight: 700 !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.35);
}

button[kind="primary"]:hover {
    transform: scale(1.03);
    box-shadow: 0 16px 36px rgba(0,0,0,0.45);
}

/* =====================
   CARDS / CONTAINERS
===================== */
.stContainer {
    background: rgba(255,255,255,0.45);
    border-radius: 24px;
    padding: 24px;
    backdrop-filter: blur(18px);
}

/* =====================
   SLIDER LABEL FIX
===================== */
.css-1cpxqw2, .css-1cpxqw2 span {
    font-weight: 600;
}

/* =====================
   REMOVE UGLY OUTLINES
===================== */
:focus {
    outline: none !important;
    box-shadow: none !important;
}

</style>
""", unsafe_allow_html=True)




# ================================
# HERO GLASS SECTION (NEW – UI ONLY)
# ================================
st.markdown("""
<style>
.hero-wrapper {
    position: relative;
    padding: 90px 40px 40px 40px;
}

.hero-glass {
    max-width: 820px;
    padding: 42px 48px;
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);
    border-radius: 28px;
    box-shadow:
        0 40px 90px rgba(0,0,0,0.22),
        0 0 0 1px rgba(255,255,255,0.35);
}

.hero-title {
    font-size: 54px;
    font-weight: 900;
    color: #030712;
    line-height: 1.1;
}

.hero-subtitle {
    font-size: 22px;
    font-weight: 600;
    margin-top: 10px;
    color: #111827;
}

.hero-desc {
    font-size: 16px;
    margin-top: 14px;
    color: #1f2937;
    max-width: 640px;
}
</style>
""", unsafe_allow_html=True)




import streamlit as st

st.markdown("""
<style>
.sidebar-btn {
    width: 100%;
    padding: 12px 16px;
    margin: 6px 0;
    border-radius: 12px;
    background: linear-gradient(135deg, #6a11cb, #2575fc);
    color: white;
    font-size: 16px;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
}
.sidebar-btn:hover {
    transform: scale(1.03);
    background: linear-gradient(135deg, #2575fc, #6a11cb);
}
.active-btn {
    background: linear-gradient(135deg, #ff512f, #dd2476);
}
</style>
""", unsafe_allow_html=True)

# --- CSS for buttons and UI enhancements ---
st.markdown("""
<style>
            
/* ===== EQUALIZER ANIMATION ===== */
.equalizer {
    display: flex;
    gap: 4px;
    height: 28px;
    align-items: flex-end;
}

.bar {
    width: 4px;
    background: linear-gradient(180deg, #1db954, #1ed760);
    animation: bounce 1.2s infinite ease-in-out;
    border-radius: 4px;
}

.bar:nth-child(1) { animation-delay: 0s }
.bar:nth-child(2) { animation-delay: .15s }
.bar:nth-child(3) { animation-delay: .3s }
.bar:nth-child(4) { animation-delay: .45s }
.bar:nth-child(5) { animation-delay: .6s }

@keyframes bounce {
    0%, 100% { height: 20% }
    50% { height: 100% }
}


/* ===== MUSIC BUTTON STYLE ===== */
.stButton > button {
    background: linear-gradient(135deg, #1db954, #1ed760);
    color: black;
    font-weight: 700;
    border-radius: 999px;
    padding: 0.65em 1.4em;
    border: none;
    transition: all 0.25s ease;
    box-shadow: 0px 4px 14px rgba(30, 215, 96, 0.45);
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 22px rgba(30, 215, 96, 0.75);
}

/* ===== PRIMARY GENERATE BUTTON ===== */
button[kind="primary"] {
    background: linear-gradient(90deg, #9333ea, #ec4899) !important;
    color: white !important;
    font-size: 18px;
    height: 3.2em;
    border-radius: 999px;
    box-shadow: 0px 0px 24px rgba(236, 72, 153, 0.65);
}

/* ===== SPOTIFY STYLE AUDIO CARD ===== */
.spotify-card {
    background: linear-gradient(145deg, #121212, #181818);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0px 8px 28px rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 20px;
}

/* ===== AUDIO PLAYER ===== */
.spotify-card audio {
    width: 100%;
    border-radius: 12px;
    filter: drop-shadow(0px 0px 14px rgba(29,185,84,0.5));
}

/* ===== AUDIO TITLE ===== */
.spotify-title {
    font-size: 18px;
    font-weight: 700;
    color: #1db954;
    margin-bottom: 8px;
}

/* ===== AUDIO META ===== */
.spotify-meta {
    font-size: 13px;
    color: #9ca3af;
    margin-bottom: 12px;
}


.example-btn button {
    background: linear-gradient(90deg, #6366f1, #3b82f6);
    color: blue;
    border-radius: 999px;
    padding: 6px 18px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    margin: 4px 6px 4px 0;
    transition: all 0.3s ease;
}

.example-btn button:hover {
    transform: scale(1.05);
    background: linear-gradient(90deg, #4f46e5, #2563eb);
    box-shadow: 0px 4px 12px rgba(99,102,241,0.4);
}

button[kind="primary"] {
    border-radius: 12px;
    height: 3em;
}
.gen-btn {
  background: linear-gradient(90deg, #f093fb, #f5576c);
  color: white;
  font-weight: bold;
  font-size: 18px;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: 0.3s;
}
.gen-btn:hover {
  transform: scale(1.05);
  box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)




# --- LOTTIE HELPER ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- QUALITY SCORE ---
class AudioQualityScorer:
    def evaluate(self, audio_path, expected_duration):
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        rms = np.sqrt(np.mean(y ** 2))
        silence_ratio = np.mean(np.abs(y) < 0.01)

        score = 100
        if abs(duration - expected_duration) > 2:
            score -= 20
        if rms < 0.03:
            score -= 20
        if silence_ratio > 0.4:
            score -= 25

        return {
            "quality_score": max(score, 0),
            "duration": round(duration, 2),
            "rms": round(rms, 4),
            "silence_ratio": round(silence_ratio, 3)
        }

def save_quality_csv(report):
    os.makedirs("outputs/quality_reports", exist_ok=True)
    path = f"outputs/quality_reports/quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=report.keys())
        writer.writeheader()
        writer.writerow(report)
    return path


# --- AUDIO ANALYSIS ---
def analyze_frequency(audio_path):
    y, sr = librosa.load(audio_path, sr=None)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    bass = np.mean(S[(freqs >= 20) & (freqs < 250)])
    mid = np.mean(S[(freqs >= 250) & (freqs < 2000)])
    high = np.mean(S[(freqs >= 2000) & (freqs < 8000)])
    return {"bass": round(bass, 4), "mid": round(mid, 4), "high": round(high, 4), "y": y, "sr": sr}

# --- LIVE WAVEFORM ANIMATION ---
def animate_waveform(duration=5, width=1000, height=200):
    placeholder = st.empty()
    y = np.random.randn(width) * 0.1
    fig, ax = plt.subplots(figsize=(10, 2))
    line, = ax.plot(y, color='#f5576c')
    ax.set_ylim([-1, 1])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Generating Audio... 🎵")
    placeholder.pyplot(fig)
    for _ in range(duration * 5):
        y = np.random.randn(width) * 0.1
        line.set_ydata(y)
        placeholder.pyplot(fig)
        time.sleep(0.2)

# ===== TASK 3.5: CACHE =====
if "cache" not in st.session_state:
    st.session_state.cache = {}




# --- SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None
if 'generation_params' not in st.session_state:
    st.session_state.generation_params = {}
if 'quality_result' not in st.session_state:
    st.session_state.quality_result = None
if 'freq_analysis' not in st.session_state:
    st.session_state.freq_analysis = None

# --- HEADER ---
st.image("assets/melodai_logo_fixed.png.jpg", width=100)
st.title("MelodAI")
st.subheader("AI-Powered Music Generator")
st.markdown("Create your custom music by describing mood, style, and context.")

# --- MUSIC LOTTIE ---
lottie_music = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_sSF6EG.json")
st_lottie(lottie_music, speed=1, width=200, height=200, key="music_anim")

# --- SIDEBAR ---
st.sidebar.header("Settings")

# --- SIDEBAR ---
st.sidebar.markdown("""
<style>
.sidebar-image img {
    border-radius: 16px;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.4);
    margin-bottom: 12px;
}
</style>

<div class="sidebar-image">
""", unsafe_allow_html=True)

st.sidebar.image("assets/background.jpg.jpeg", use_container_width=True)

st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.header("Settings")

duration = st.sidebar.slider("Duration (seconds)", 10, 120, 30)
temperature = st.sidebar.slider("Creativity (0.1-2.0)", 0.1, 2.0, 1.0)

# ---------------------------------------------------------
# Sidebar controls - Compact & Modern
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ Generation Settings")

# Model selection with enhanced UI
model_choice = st.sidebar.selectbox(
    "🤖 Model Quality",
    ["Fast (Small)", "Balanced (Medium)", "Best (Large)", "Melody"],
    help="Higher quality = slower generation"
)

# Map model choice to actual model names
model_mapping = {
    "Fast (Small)": "facebook/musicgen-small",
    "Balanced (Medium)": "facebook/musicgen-medium",
    "Best (Large)": "facebook/musicgen-large",
    "Melody": "facebook/musicgen-melody"
}
model_name = model_mapping[model_choice]

# Display model information
model_info = {
    "Fast (Small)": {
        "params": "300M",
        "time": "~15-30s",
        "uses": "Quick drafts, prototypes",
        "memory": "Low"
    },
    "Balanced (Medium)": {
        "params": "1.5B",
        "time": "~30-60s",
        "uses": "Standard quality music",
        "memory": "Medium"
    },
    "Best (Large)": {
        "params": "3.3B",
        "time": "~60-120s",
        "uses": "Professional quality",
        "memory": "High"
    },
    "Melody": {
        "params": "1.5B",
        "time": "~30-60s",
        "uses": "Melody-focused generation",
        "memory": "Medium"
    }
}

info = model_info[model_choice]
st.sidebar.markdown(f"""
<div style="background: rgba(139, 92, 246, 0.1); border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 3px solid #8b5cf6;">
    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;"><strong>Model Info:</strong></div>
    <div style="font-size: 11px; color: #475569;">
        📊 {info['params']} params • ⏱️ {info['time']} • 💾 {info['memory']}<br>
        🎯 {info['uses']}
    </div>
</div>
""", unsafe_allow_html=True)


# Advanced parameters
with st.sidebar.expander("Advanced Parameters"):
    top_k = st.slider("Top-K", 0, 100, 50)
    top_p = st.slider("Top-P", 0.0, 1.0, 0.9)
    cfg = st.slider("CFG Coefficient", 0.0, 5.0, 1.0)
    expert_mode = st.checkbox("Expert Mode")




# ===== CACHE STATS =====
st.sidebar.markdown("### ⚡ Cache")
st.sidebar.metric("Cached Tracks", len(st.session_state.cache))

if st.sidebar.button("Clear Cache"):
    st.session_state.cache.clear()
    st.sidebar.success("Cache cleared")

# Preset configurations
st.sidebar.markdown("#### 🎛️ Quick Presets")
preset_col1, preset_col2 = st.columns(2)
with preset_col1:
    if st.sidebar.button("⚡ Quick Draft", key="preset_quick", use_container_width=True):
        st.session_state.preset_duration = 15
        st.session_state.preset_temperature = 0.8
        st.session_state.preset_model = "Fast (Small)"
        st.success("Quick Draft preset loaded!")
with preset_col2:
    if st.sidebar.button("📊 Standard", key="preset_standard", use_container_width=True):
        st.session_state.preset_duration = 30
        st.session_state.preset_temperature = 1.0
        st.session_state.preset_model = "Balanced (Medium)"
        st.success("Standard preset loaded!")

preset_col3, preset_col4 = st.columns(2)
with preset_col3:
    if st.sidebar.button("🎵 Professional", key="preset_pro", use_container_width=True):
        st.session_state.preset_duration = 60
        st.session_state.preset_temperature = 1.2
        st.session_state.preset_model = "Best (Large)"
        st.success("Professional preset loaded!")
with preset_col4:
    if st.sidebar.button("🎨 Custom", key="preset_custom", use_container_width=True):
        # Reset to defaults
        if "preset_duration" in st.session_state: del st.session_state.preset_duration
        if "preset_temperature" in st.session_state: del st.session_state.preset_temperature
        if "preset_model" in st.session_state: del st.session_state.preset_model
        st.success("Reset to custom settings!")


# Apply presets if set
duration = st.session_state.get("preset_duration", 30)
temperature = st.session_state.get("preset_temperature", 1.0)
if "preset_model" in st.session_state:
    model_choice = st.session_state.preset_model
    

# ===== AGGREGATE FEEDBACK =====
if st.session_state.get("feedback"):
    ratings = [f["rating"] for f in st.session_state.feedback]
    avg_rating = round(sum(ratings) / len(ratings), 2)

    st.sidebar.markdown("### ⭐ Feedback Stats")
    st.sidebar.metric("Average Rating", avg_rating)

    categories = [f["category"] for f in st.session_state.feedback]
    most_common = max(set(categories), key=categories.count)
    st.sidebar.caption(f"Most common feedback: **{most_common}**")



# --- INPUT ---
st.markdown("### Describe Your Music")
user_input = st.text_area(
    "Enter your music description",
    placeholder="E.g., energetic workout music with electronic beats",
    height=100
)
mood = st.selectbox("Quick Mood", list(EXAMPLES.keys()))
context = st.multiselect("Context/Situation", ["Work", "Party", "Sleep", "Exercise", "Study", "Relaxation"])

st.markdown("**Try an example prompt:**")

cols = st.columns(5)
for i, prompt in enumerate(EXAMPLES[mood][:5]):
    with cols[i]:
        if st.markdown('<div class="example-btn">', unsafe_allow_html=True):
            pass
        if st.button(prompt, key=f"ex_{i}"):
            user_input = prompt
        st.markdown('</div>', unsafe_allow_html=True)


# ===== TASK 3.3: AUTO MODEL SELECTION =====
if model_choice == "auto":
    if duration > 60:
        model_choice = "small"
    elif duration > 30:
        model_choice = "medium"
    else:
        model_choice = "large"





# --- GENERATE MUSIC BUTTON ---
if st.button("🎶Generate Music", key="gen_music", use_container_width=True):

    if len(user_input.strip()) > 0:

        cache_key = Cache_Manager.make_key(
            user_input, duration, temperature, model_choice
        )

        cached_audio = Cache_Manager.get(cache_key)

        if cached_audio:
            st.session_state.current_audio = cached_audio
            st.success("⚡ Loaded from cache!")
        else:
            with st.spinner("🎵 Generating your music... Please wait!"):
                animate_waveform(duration=5)

                audio_file, params, prompt = generate_music_pipeline(
                    user_input,
                    duration=duration,
                    temperature=temperature,
                    model=model_choice
                )

                Cache_Manager.set(cache_key, audio_file)

                st.session_state.current_audio = audio_file
                st.session_state.generation_params = {
                    "prompt": prompt,
                    "duration": duration,
                    "temperature": temperature,
                    "model": model_choice,
                    "mood": mood,
                    "context": context
                }

                # Quality scoring
                scorer = AudioQualityScorer()
                quality = scorer.evaluate(audio_file, duration)
                quality["prompt"] = prompt
                quality["file"] = audio_file
                st.session_state.quality_result = quality
                save_quality_csv(quality)

                # Frequency analysis
                analysis = analyze_frequency(audio_file)
                st.session_state.freq_analysis = analysis

            


    

            # --- QUALITY SCORE ---
            scorer = AudioQualityScorer()
            quality = scorer.evaluate(audio_file, duration)
            quality["prompt"] = prompt
            quality["file"] = audio_file
            st.session_state.quality_result = quality
            save_quality_csv(quality)

            # --- AUDIO ANALYSIS ---
            analysis = analyze_frequency(audio_file)
            st.session_state.freq_analysis = analysis

        st.success("Music generation complete!")




# --- OUTPUT DISPLAY ---
if st.session_state.current_audio:
    


    st.markdown("""
    <div class="spotify-card">
        <div class="spotify-title">🎶 Generated Track</div>
        <div class="spotify-meta">MelodAI • AI Music Studio</div>
""", unsafe_allow_html=True)

    st.audio(st.session_state.current_audio, format='audio/wav')

    st.markdown("</div>", unsafe_allow_html=True)



    with open(st.session_state.current_audio, "rb") as f:
        st.download_button(
            label="Download Audio",
            data=f,
            file_name=f"melodai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
            mime="audio/wav"
        )

     

    # --- QUALITY SCORE UI ---
    if st.session_state.quality_result:
        st.markdown("## 🎯 Audio Quality Score")
        q = st.session_state.quality_result
        c1, c2, c3 = st.columns(3)
        c1.metric("Quality Score", f"{q['quality_score']}/100")
        c2.metric("Duration (s)", q["duration"])
        c3.metric("Silence Ratio", q["silence_ratio"])
        st.progress(q["quality_score"]/100)


# ===== TASK 3.2: USER FEEDBACK =====
st.markdown("## 💬 Your Feedback")

if "feedback" not in st.session_state:
    st.session_state.feedback = []

rating = st.slider("⭐ Rate this track", 1, 5, 3)
feedback_category = st.selectbox(
    "What best describes this track?",
    [
        "Perfect!",
        "Doesn't match mood",
        "Poor audio quality",
        "Too repetitive"
    ]
)
comment = st.text_area("Optional comment")

col_f1, col_f2 = st.columns(2)
thumbs_up = col_f1.button("👍 Like")
thumbs_down = col_f2.button("👎 Dislike")

if st.button("Submit Feedback"):
    st.session_state.feedback.append({
        "rating": rating,
        "category": feedback_category,
        "comment": comment,
        "timestamp": current_timestamp()
    })
    st.success("Thanks for your feedback ❤️")



# --- WAVEFORM & FREQUENCY ---
if st.session_state.freq_analysis:
        analysis = st.session_state.freq_analysis
        y = analysis["y"]
        sr = analysis["sr"]

        st.subheader("Waveform")
        fig1, ax1 = plt.subplots(figsize=(10,3))
        librosa.display.waveshow(y, sr=sr, color='#f5576c')
        ax1.set_title("Audio Waveform")
        st.pyplot(fig1)

        st.subheader("Frequency Energy Distribution")
        fig2, ax2 = plt.subplots(figsize=(6,4))
        ax2.bar(
            ["Bass", "Mid", "High"],
            [analysis["bass"], analysis["mid"], analysis["high"]],
            color=['#f093fb', '#9be7ff', '#f5576c']
        )
        ax2.set_ylabel("Energy")
        ax2.set_title("Bass / Mid / High Frequency Energy")
        st.pyplot(fig2)


from backend.audio_processor import AudioProcessor
import streamlit as st
import os

st.markdown("## 🎚️ Audio Enhancement")

processor = AudioProcessor()

preset = st.radio(
    "Choose enhancement style",
    ["studio", "concert", "bedroom"],
    horizontal=True
)

if "generated_audio_path" in st.session_state:
    if st.button("✨ Enhance Audio"):
        with st.spinner("Enhancing audio..."):
            enhanced_path = processor.enhance(
                st.session_state.generated_audio_path,
                preset
            )

            st.success("Audio enhanced successfully!")

            st.audio(enhanced_path)

            with open(enhanced_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Enhanced Audio",
                    data=f,
                    file_name=os.path.basename(enhanced_path),
                    mime="audio/wav"
                )
else:
    st.info("Generate music first to enable enhancement.")



# --- HISTORY & ADVANCED FEATURES ---
st.sidebar.markdown("### 🕑 History (Last 10 Generations)")

def add_to_history(prompt, audio_file, params):
    st.session_state.history.append({
        "id": generate_unique_id(),
        "timestamp": current_timestamp(),
        "prompt": prompt,
        "audio_file": audio_file,
        "params": params,
        "favorite": False
    })

if st.session_state.current_audio:
    add_to_history(user_input, st.session_state.current_audio, st.session_state.generation_params)

for item in st.session_state.history[-10:]:
    st.sidebar.markdown(f"**{item['timestamp']}**")
    st.sidebar.write(item['prompt'])
    st.sidebar.audio(item['audio_file'])

# --- Variations / Extend Music ---
st.markdown("---")
st.markdown("### ⚡ Advanced Features")
if st.button("Generate 3 Variations"):
    variations = generate_variations(user_input, num_variations=3, duration=duration)
    for v in variations:
        st.audio(v, format="audio/mp3")

if st.button("Extend Music +30s"):
    if st.session_state.current_audio:
        extended_audio = extend_music(user_input, extension_duration=30)
        st.audio(extended_audio, format="audio/mp3")
