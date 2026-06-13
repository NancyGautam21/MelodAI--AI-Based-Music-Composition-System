import streamlit as st

st.title("ℹ About MelodAI")

st.write("""
MelodAI converts text prompts into music using AI.

### Features:
- Generate music from text
- Save and download audio
- View audio history in library
- Multi-page Streamlit UI

More features will be added in the next tasks.""")


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
            background: rgba(255, 255, 255, 0.15);
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
            background: rgba(255, 255, 255, 0.15);
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