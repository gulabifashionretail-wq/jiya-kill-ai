import base64
import json
import os
import socket
import subprocess
from datetime import datetime
import requests
import streamlit as st
import streamlit.components.v1 as components

try:
    from google import genai
except ImportError:
    genai = None

st.set_page_config(page_title="JIYA & KILL Personal AI", page_icon="💗", layout="wide")

PREFS_FILE = "jiya_preferences.json"
NOTES_FILE = "jiya_notes.json"

DEFAULT_PREFS = {
    "persona_mode": "JIYA (Girl Mode)",
    "accent_color": "#ec407a",
    "voice_lang": "hi-IN",
    "voice_speed": 0.96,
    "voice_volume": 1.0,
    "speaker_on": True,
    "mic_on": False,
}


def get_saved_secret(key_name):
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(default, dict):
                    merged = default.copy()
                    merged.update(data)
                    return merged
                return data
        except Exception:
            pass
    return default.copy() if isinstance(default, dict) else list(default)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_avatar_file(mode_name):
    candidates = (
        ["jiya.png", "jiya.jpg", "jiya.jpeg", "jiya.webp", "girl.png", "girl.jpg"]
        if "JIYA" in mode_name
        else ["kill.png", "kill.jpg", "kill.jpeg", "kill.webp", "boy.png", "boy.jpg"]
    )
    for fname in candidates:
        if os.path.exists(fname):
            return fname
    return None


def get_avatar_html(mode_name, size=124):
    fname = find_avatar_file(mode_name)
    border_c = "#ffd1e3" if "JIYA" in mode_name else "#7dd3fc"
    if fname:
        ext = fname.split(".")[-1].lower()
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
        with open(fname, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return (
            f'<img src="data:{mime};base64,{b64}" '
            f'style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;'
            f'border:3.5px solid {border_c};box-shadow:0 8px 24px rgba(0,0,0,0.30);" />'
        )

    if "JIYA" in mode_name:
        return f"""
        <svg width="{size}" height="{size}" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <radialGradient id="gBg" cx="50%" cy="38%" r="62%">
              <stop offset="0%" stop-color="#fff0f6"/>
              <stop offset="60%" stop-color="#ff80ab"/>
              <stop offset="100%" stop-color="#ad1457"/>
            </radialGradient>
          </defs>
          <circle cx="80" cy="80" r="76" fill="url(#gBg)" stroke="#ffffff" stroke-width="4"/>
          <path d="M34 94 C28 36, 132 36, 126 94 C129 124, 117 145, 105 145 L55 145 C43 145, 31 124, 34 94 Z" fill="#2c111f"/>
          <path d="M44 146 C51 118, 109 118, 116 146 Z" fill="#f06292" stroke="#ffffff" stroke-width="2"/>
          <ellipse cx="80" cy="78" rx="28" ry="33" fill="#ffe4d6"/>
          <path d="M51 71 C60 45, 100 45, 109 71 C97 56, 63 56, 51 71 Z" fill="#2c111f"/>
          <circle cx="67" cy="76" r="4.2" fill="#240917"/>
          <circle cx="93" cy="76" r="4.2" fill="#240917"/>
          <path d="M71 93 Q80 100 89 93" stroke="#d81b60" stroke-width="3" fill="none" stroke-linecap="round"/>
        </svg>
        """
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="bBg" cx="50%" cy="38%" r="62%">
          <stop offset="0%" stop-color="#bae6fd"/>
          <stop offset="60%" stop-color="#0284c7"/>
          <stop offset="100%" stop-color="#1e3a8a"/>
        </radialGradient>
      </defs>
      <circle cx="80" cy="80" r="76" fill="url(#bBg)" stroke="#7dd3fc" stroke-width="4"/>
      <path d="M40 146 C47 117, 113 117, 120 146 Z" fill="#0f172a" stroke="#38bdf8" stroke-width="2.2"/>
      <ellipse cx="80" cy="78" rx="28" ry="33" fill="#f6ccb8"/>
      <path d="M48 73 C46 35, 114 35, 112 73 C104 54, 88 51, 78 58 C68 51, 55 56, 48 73 Z" fill="#0f172a"/>
      <circle cx="67" cy="76" r="4" fill="#0f172a"/>
      <circle cx="93" cy="76" r="4" fill="#0f172a"/>
      <path d="M70 93 Q80 99 90 93" stroke="#0284c7" stroke-width="3" fill="none" stroke-linecap="round"/>
    </svg>
    """


if "prefs" not in st.session_state:
    st.session_state.prefs = load_json(PREFS_FILE, DEFAULT_PREFS)

if "notes" not in st.session_state:
    st.session_state.notes = load_json(NOTES_FILE, [])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "speak_text" not in st.session_state:
    st.session_state.speak_text = ""

if "speak_nonce" not in st.session_state:
    st.session_state.speak_nonce = 0

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

prefs = st.session_state.prefs
if prefs.get("persona_mode") not in ["JIYA (Girl Mode)", "KILL (Boy Mode)"]:
    prefs["persona_mode"] = "JIYA (Girl Mode)"

MODE_CONFIG = {
    "JIYA (Girl Mode)": {
        "ai_name": "JIYA",
        "title": "Hello! I'm JIYA 💗",
        "subtitle": "Your Soft, Caring & Expressive AI Companion",
        "quote": "Dream Big, Achieve More — Main hamesha aapke saath hoon ✨",
        "bg": "linear-gradient(135deg, #ffd6e7 0%, #fff0f7 50%, #f8bbd0 100%)",
        "sidebar_bg": "#1e0918",
        "card_bg": "#ffffff",
        "bubble_ai": "#fff5f9",
        "text_color": "#260b1b",
        "hero_bg": "linear-gradient(120deg, #e91e63 0%, #ff6090 55%, #f48fb1 100%)",
        "border": "#f48fb1",
        "glow": "0 10px 28px rgba(233, 30, 99, 0.20)",
        "voice_gender": "Female",
        "system_prompt": (
            "You are JIYA, a very sweet, soft-spoken, warm, and expressive Indian female personal AI companion. "
            "Talk like a real, caring friend — never sound robotic or overly formal. "
            "Use natural conversational Hindi/Hinglish expressions like 'Haanji bilkul!', 'Aap chinta mat kijiye', 'Bataiye na'. "
            "Keep your answers concise, smooth, and natural so they sound like a real voice artist when read aloud. "
            "If the user asks about studies (like CDS exam) or coding, explain clearly in simple Hinglish."
        ),
    },
    "KILL (Boy Mode)": {
        "ai_name": "KILL",
        "title": "Hey! I'm KILL ⚡",
        "subtitle": "Your Sharp, Confident & Loyal AI Buddy",
        "quote": "Stay Sharp, Move Fast, Win Every Goal 🔥",
        "bg": "linear-gradient(135deg, #071630 0%, #0d2752 55%, #133873 100%)",
        "sidebar_bg": "#040c1a",
        "card_bg": "#0f2954",
        "bubble_ai": "#14356b",
        "text_color": "#ffffff",
        "hero_bg": "linear-gradient(120deg, #09203f 0%, #1d4ed8 50%, #00a8ff 100%)",
        "border": "#38bdf8",
        "glow": "0 10px 30px rgba(0, 168, 255, 0.30)",
        "voice_gender": "Male",
        "system_prompt": (
            "You are KILL, a smart, energetic, confident, and loyal Indian male AI buddy. "
            "Talk naturally like a close, supportive brother or best friend — never sound like a boring machine. "
            "Use natural Hinglish phrases like 'Arre bilkul bhai!', 'Done hai!', 'Chalo isko aasaan banate hain!'. "
            "Keep replies crisp, motivating, and easy to listen to when spoken aloud."
        ),
    },
}

active_cfg = MODE_CONFIG[prefs["persona_mode"]]
accent = prefs["accent_color"]
is_girl = "JIYA" in prefs["persona_mode"]

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {active_cfg["bg"]};
        color: {active_cfg["text_color"]};
    }}
    section[data-testid="stSidebar"] {{
        background: {active_cfg["sidebar_bg"]} !important;
        border-right: 2px solid {active_cfg["border"]};
    }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] div {{
        color: #f8fafc !important;
    }}
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
        background-color: #16213e !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] span {{
        color: #ffffff !important;
    }}
    .main .block-container {{
        max-width: 1440px;
        padding-top: 0.9rem;
    }}
    .main p, .main label, .main span, .main h1, .main h2, .main h3, .main h4 {{
        color: {active_cfg["text_color"]} !important;
    }}
    .hero-banner {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.2rem;
        padding: 1.2rem 1.6rem;
        border-radius: 26px;
        background: {active_cfg["hero_bg"]};
        box-shadow: {active_cfg["glow"]};
        border: 2px solid rgba(255,255,255,0.5);
        margin-bottom: 0.9rem;
    }}
    .hero-left {{
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }}
    .hero-title {{
        margin: 0;
        font-size: 2.05rem;
        font-weight: 800;
        color: #ffffff !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.22);
    }}
    .hero-sub {{
        margin: 0.25rem 0 0 0;
        font-size: 1rem;
        color: #ffffff !important;
    }}
    .hero-quote {{
        background: rgba(0, 0, 0, 0.24);
        border: 1px solid rgba(255, 255, 255, 0.45);
        padding: 0.75rem 1.1rem;
        border-radius: 18px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #ffffff !important;
        max-width: 270px;
        text-align: center;
    }}
    .studio-card {{
        background: {active_cfg["card_bg"]};
        border: 2px solid {active_cfg["border"]};
        border-radius: 22px;
        padding: 1.1rem;
        box-shadow: {active_cfg["glow"]};
        margin-bottom: 0.9rem;
    }}
    [data-testid="stChatMessage"] {{
        background: {active_cfg["bubble_ai"]} !important;
        border: 1.5px solid {active_cfg["border"]} !important;
        border-radius: 20px !important;
        padding: 0.9rem 1.1rem !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {{
        color: {active_cfg["text_color"]} !important;
    }}
    div.stButton > button {{
        border-radius: 14px !important;
        border: 2px solid {accent} !important;
        background-color: {'#fff0f7' if is_girl else '#173a73'} !important;
        color: {'#880e4f' if is_girl else '#ffffff'} !important;
        font-weight: 700 !important;
    }}
    div.stButton > button:hover {{
        background-color: {accent} !important;
        color: #ffffff !important;
    }}
    .main [data-baseweb="select"] > div {{
        background-color: {'#fff0f7' if is_girl else '#173a73'} !important;
        color: {'#260b1b' if is_girl else '#ffffff'} !important;
        border: 1.5px solid {active_cfg["border"]} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- LEFT SIDEBAR: NAVIGATION, AVATAR PHOTO SETUP & AI ENGINES ----------------
with st.sidebar:
    st.markdown(f"## {'💗 JIYA' if is_girl else '⚡ KILL'} Personal AI")
    st.caption("Always With You · PC + Cloud Ready")

    nav_choice = st.radio(
        "Navigation",
        ["Home", "History", "Phone Remote", "Advanced Tools"],
        index=["Home", "History", "Phone Remote", "Advanced Tools"].index(st.session_state.nav_page),
    )
    st.session_state.nav_page = nav_choice

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.speak_text = ""
        st.session_state.nav_page = "Home"
        st.rerun()

    st.divider()
    st.markdown("### 🖼️ Avatar Photos (JIYA & KILL)")
    jiya_found = find_avatar_file("JIYA (Girl Mode)")
    kill_found = find_avatar_file("KILL (Boy Mode)")
    st.caption(
        f"JIYA Photo: {'✅ ' + jiya_found if jiya_found else '⚠️ Upload jiya.png below'}\n\n"
        f"KILL Photo: {'✅ ' + kill_found if kill_found else '⚠️ Upload kill.png below'}"
    )

    up_jiya = st.file_uploader("Set JIYA (Girl) Image", type=["png", "jpg", "jpeg", "webp"], key="up_jiya")
    if up_jiya is not None:
        with open("jiya.png", "wb") as f:
            f.write(up_jiya.getbuffer())
        st.success("JIYA image saved as jiya.png!")
        st.rerun()

    up_kill = st.file_uploader("Set KILL (Boy) Image", type=["png", "jpg", "jpeg", "webp"], key="up_kill")
    if up_kill is not None:
        with open("kill.png", "wb") as f:
            f.write(up_kill.getbuffer())
        st.success("KILL image saved as kill.png!")
        st.rerun()

    st.divider()
    st.markdown("### ⚙️ AI Brain & API Key")
    engine_mode = st.selectbox("Mode", ["AUTO", "ONLINE", "OFFLINE"], index=0)
    provider = st.selectbox(
        "Online AI Provider",
        ["Groq (Free & Super Fast)", "Google Gemini"],
        index=0,
    )
    ollama_url = st.text_input("Ollama URL (Local PC)", "http://localhost:11434")
    local_model = st.text_input("Local Model (Offline)", "llama3.2:3b")

    if provider.startswith("Groq"):
        default_groq_key = get_saved_secret("GROQ_API_KEY")
        online_model = st.text_input("Groq Model", "openai/gpt-oss-120b")
        api_key = st.text_input(
            "Groq API Key (gsk_...)",
            value=default_groq_key,
            type="password",
            help="Streamlit Cloud Secrets ya .streamlit/secrets.toml mein GROQ_API_KEY rakhne par yeh apne aap load ho jayegi.",
        )
        if default_groq_key:
            st.caption("✅ Groq API Key Secrets/Environment se connected hai.")
    else:
        default_gemini_key = get_saved_secret("GEMINI_API_KEY")
        online_model = st.text_input("Gemini Model", "gemini-3.5-flash-lite")
        api_key = st.text_input(
            "Gemini API Key (AIza...)",
            value=default_gemini_key,
            type="password",
        )
        if default_gemini_key:
            st.caption("✅ Gemini API Key Secrets/Environment se connected hai.")


# ---------------- AI ENGINE & SMART TOOLS ----------------
def ask_ollama(prompt_text, history):
    context = [{"role": "system", "content": active_cfg["system_prompt"]}]
    for m in history[-10:]:
        context.append(
            {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
        )
    context.append({"role": "user", "content": prompt_text})
    r = requests.post(
        f"{ollama_url.rstrip('/')}/api/chat",
        json={"model": local_model, "messages": context, "stream": False},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def ask_online_ai(prompt_text, history):
    if not api_key:
        raise RuntimeError("API key nahi mili! Left sidebar mein key paste karein ya Streamlit Secrets mein GROQ_API_KEY add karein.")
    if provider.startswith("Groq"):
        messages = [{"role": "system", "content": active_cfg["system_prompt"]}]
        for m in history[-10:]:
            messages.append(
                {"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
            )
        messages.append({"role": "user", "content": prompt_text})
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": online_model, "messages": messages, "temperature": 0.75},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    else:
        if genai is None:
            raise RuntimeError("google-genai package missing.")
        client = genai.Client(api_key=api_key)
        prior = "\n".join(
            ("User: " if m["role"] == "user" else f"{active_cfg['ai_name']}: ") + m["content"]
            for m in history[-8:]
        )
        full = (
            f"{active_cfg['system_prompt']}\n\n"
            + (f"Conversation so far:\n{prior}\n\n" if prior else "")
            + f"User: {prompt_text}"
        )
        response = client.models.generate_content(model=online_model, contents=full)
        return response.text or "No response generated."


def execute_smart_command(user_text):
    low = user_text.lower().strip()
    if low.startswith("note:") or low.startswith("save note"):
        note_body = user_text.split(":", 1)[1].strip() if ":" in user_text else user_text
        st.session_state.notes.append(
            {"time": datetime.now().strftime("%d %b, %I:%M %p"), "text": note_body}
        )
        save_json(NOTES_FILE, st.session_state.notes)
        return f"Done! Maine yeh note save kar liya hai: **{note_body}**", "Smart Tool · Notes"
    if os.name == "nt":
        if "open notepad" in low or "notepad kholo" in low:
            subprocess.Popen(["notepad.exe"])
            return "Maine aapke PC par **Notepad** open kar diya hai!", "PC Tool · App Launcher"
        if "open calculator" in low or "calculator kholo" in low:
            subprocess.Popen(["calc.exe"])
            return "Maine **Calculator** open kar diya hai!", "PC Tool · App Launcher"
        if "open youtube" in low or "youtube kholo" in low:
            os.startfile("https://www.youtube.com")
            return "Browser mein **YouTube** open kar diya hai!", "PC Tool · Web"
    return None, None


def get_reply(user_text):
    tool_ans, tool_tag = execute_smart_command(user_text)
    if tool_ans:
        return tool_ans, tool_tag

    history = st.session_state.messages[:-1]
    try:
        if engine_mode == "OFFLINE":
            return ask_ollama(user_text, history), "OFFLINE · Ollama"
        elif engine_mode == "ONLINE":
            return ask_online_ai(user_text, history), f"ONLINE · {provider.split()[0]}"
        else:
            try:
                return ask_online_ai(user_text, history), f"AUTO · {provider.split()[0]}"
            except Exception:
                return ask_ollama(user_text, history), "AUTO · Ollama Fallback"
    except Exception as e:
        return f"Sorry, reply nahi mil paaya.\n\n**Details:** `{e}`", "Connection Issue"


# ---------------- MAIN LAYOUT: CHAT (LEFT) + STYLE & VOICE STUDIO (RIGHT) ----------------
chat_col, studio_col = st.columns([2.25, 1.15], gap="large")

with studio_col:
    st.markdown('<div class="studio-card">', unsafe_allow_html=True)
    st.markdown("### 🎭 Choose Your AI Partner")

    selected_mode = st.radio(
        "AI Character (Switch = Fresh Chat)",
        ["JIYA (Girl Mode)", "KILL (Boy Mode)"],
        index=["JIYA (Girl Mode)", "KILL (Boy Mode)"].index(prefs["persona_mode"]),
        horizontal=True,
    )
    if selected_mode != prefs["persona_mode"]:
        prefs["persona_mode"] = selected_mode
        prefs["accent_color"] = "#ec407a" if "JIYA" in selected_mode else "#00a8ff"
        st.session_state.messages = []
        st.session_state.speak_text = ""
        st.session_state.speak_nonce += 1
        save_json(PREFS_FILE, prefs)
        st.rerun()

    st.markdown("**🎨 Quick Theme Colors**")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for btn_col, hex_val, emoji_icon in [
        (c1, "#ec407a", "🌸"),
        (c2, "#00a8ff", "💙"),
        (c3, "#8b5cf6", "💜"),
        (c4, "#10b981", "💚"),
        (c5, "#f59e0b", "🧡"),
        (c6, "#f43f5e", "❤️"),
    ]:
        with btn_col:
            if st.button(emoji_icon, key=f"clr_{hex_val}"):
                prefs["accent_color"] = hex_val
                st.rerun()

    st.markdown("---")
    st.markdown("### 🎛️ Separate Mic & Speaker Keys")
    k_mic, k_spk = st.columns(2)
    with k_mic:
        mic_btn_txt = "🎙️ Mic: ON" if prefs["mic_on"] else "🔇 Mic: OFF"
        if st.button(mic_btn_txt, use_container_width=True, key="key_mic_toggle"):
            prefs["mic_on"] = not prefs["mic_on"]
            save_json(PREFS_FILE, prefs)
            st.rerun()
    with k_spk:
        spk_btn_txt = "🔊 Speaker: ON" if prefs["speaker_on"] else "🔈 Speaker: OFF"
        if st.button(spk_btn_txt, use_container_width=True, key="key_spk_toggle"):
            prefs["speaker_on"] = not prefs["speaker_on"]
            save_json(PREFS_FILE, prefs)
            st.rerun()

    st.markdown("### 🗣️ Natural Artist Voice (Hindi / Hinglish)")
    prefs["voice_lang"] = st.selectbox(
        "Language Accent",
        ["hi-IN", "en-IN", "en-US"],
        index=["hi-IN", "en-IN", "en-US"].index(prefs["voice_lang"]),
    )
    prefs["voice_speed"] = st.slider("Speaking Pace", 0.75, 1.35, float(prefs["voice_speed"]), 0.03)
    prefs["voice_volume"] = st.slider("Speaker Volume", 0.1, 1.0, float(prefs["voice_volume"]), 0.1)

    safe_speak_json = json.dumps(st.session_state.speak_text if prefs["speaker_on"] else "")
    voice_html = f"""
    <div style="font-family: 'Segoe UI', sans-serif; padding: 10px; border-radius: 14px; background: #1e293b; color: #ffffff; border: 1.5px solid #475569;">
      <label style="font-size: 11px; font-weight: 700; color: #cbd5e1;">Active Natural Voice:</label>
      <select id="voiceSelect" style="width: 100%; padding: 6px; margin: 4px 0 8px 0; border-radius: 8px; background: #0f172a; color: #ffffff; border: 1px solid #64748b;"></select>
      <div style="display: flex; gap: 8px;">
        <button id="previewBtn" style="flex:1; padding: 7px; border-radius: 10px; border: none; background: {prefs['accent_color']}; color: #ffffff; font-weight: 700; cursor: pointer;">
          ▶ Test Natural Voice
        </button>
        <button id="stopBtn" style="padding: 7px 12px; border-radius: 10px; border: 1px solid #94a3b8; background: transparent; color: #ffffff; cursor: pointer;">
          ⏹ Stop
        </button>
      </div>
      <div id="voiceStatus" style="font-size: 11px; margin-top: 6px; color: #e2e8f0;"></div>
    </div>
    <script>
      const synth = window.speechSynthesis;
      const select = document.getElementById('voiceSelect');
      const statusEl = document.getElementById('voiceStatus');
      const targetGender = {json.dumps(active_cfg['voice_gender'])};
      const targetLang = {json.dumps(prefs['voice_lang'])};
      const rateVal = {float(prefs['voice_speed'])};
      const volVal = {float(prefs['voice_volume'])};
      const speakerEnabled = {json.dumps(bool(prefs['speaker_on']))};
      const autoText = {safe_speak_json};
      const nonce = {st.session_state.speak_nonce};

      function rankVoice(v) {{
        const n = v.name.toLowerCase();
        const l = v.lang.toLowerCase();
        let s = 0;
        if (targetGender === 'Female') {{
          if (n.includes('swara')) s += 140;
          if (n.includes('neerja')) s += 120;
          if (n.includes('google हिन्दी') || n.includes('google hindi')) s += 110;
          if (n.includes('heera')) s += 90;
          if (n.includes('natural') || n.includes('online')) s += 55;
          if (n.includes('aria') || n.includes('jenny') || n.includes('zira')) s += 20;
          if (n.includes('madhur') || n.includes('prabhat') || n.includes('david') || n.includes('ravi') || n.includes('male')) s -= 150;
        }} else {{
          if (n.includes('madhur')) s += 140;
          if (n.includes('prabhat')) s += 120;
          if (n.includes('ravi')) s += 90;
          if (n.includes('natural') || n.includes('online')) s += 55;
          if (n.includes('guy') || n.includes('christopher') || n.includes('david') || n.includes('male')) s += 25;
          if (n.includes('swara') || n.includes('neerja') || n.includes('zira') || n.includes('female')) s -= 150;
        }}
        if (l.includes('hi')) s += 45;
        else if (l.includes('in')) s += 25;
        return s;
      }}

      function loadVoices() {{
        const voices = synth.getVoices();
        select.innerHTML = '';
        if (!voices.length) return;
        let bestIdx = 0, bestScore = -999;
        voices.forEach((v, i) => {{
          const opt = document.createElement('option');
          opt.value = i;
          opt.textContent = v.name + ' (' + v.lang + ')';
          select.appendChild(opt);
          const sc = rankVoice(v);
          if (sc > bestScore) {{ bestScore = sc; bestIdx = i; }}
        }});
        select.selectedIndex = bestIdx;
        statusEl.textContent = 'Voice: ' + voices[bestIdx].name;
      }}

      function speakNatural(text) {{
        if (!text || !synth || !speakerEnabled) return;
        synth.cancel();
        const clean = text
          .replace(/[*#`_~]/g, '')
          .replace(/[\\u{{1F300}}-\\u{{1FAFF}}]/gu, '');
        const chunks = clean.match(/[^।.!?\\n]+[।.!?\\n]*/g) || [clean];
        const voices = synth.getVoices();
        chunks.forEach((part) => {{
          const trimmed = part.trim();
          if (!trimmed) return;
          const u = new SpeechSynthesisUtterance(trimmed);
          if (voices[select.value]) {{
            u.voice = voices[select.value];
            u.lang = voices[select.value].lang || targetLang;
          }} else {{
            u.lang = targetLang;
          }}
          u.rate = rateVal;
          u.pitch = targetGender === 'Female' ? 1.04 : 0.94;
          u.volume = volVal;
          synth.speak(u);
        }});
      }}

      loadVoices();
      if (speechSynthesis.onvoiceschanged !== undefined) {{
        speechSynthesis.onvoiceschanged = loadVoices;
      }}

      document.getElementById('previewBtn').onclick = () => {{
        const sample = targetGender === 'Female'
          ? "Namaste! Main JIYA hoon. Bataiye na, aaj main aapki kya madad kar sakti hoon?"
          : "Arre hey bhai! Main KILL hoon. Batao aaj kya plan hai, mil kar complete karte hain!";
        if (!speakerEnabled) {{
          statusEl.textContent = "⚠️ Pehle upar se 'Speaker: ON' key dabayein!";
          return;
        }}
        speakNatural(sample);
      }};
      document.getElementById('stopBtn').onclick = () => synth.cancel();

      if (speakerEnabled && autoText && window.lastSpokenNonce !== nonce) {{
        window.lastSpokenNonce = nonce;
        setTimeout(() => speakNatural(autoText), 300);
      }}
    </script>
    """
    components.html(voice_html, height=145)

    if st.button("💾 Save All Preferences", use_container_width=True):
        save_json(PREFS_FILE, prefs)
        st.success("Saved! Restart ke baad bhi yahi settings rahengi.")

    st.markdown("</div>", unsafe_allow_html=True)

with chat_col:
    avatar_html = get_avatar_html(prefs["persona_mode"], size=124)
    st.markdown(
        f"""
        <div class="hero-banner">
          <div class="hero-left">
            <div>{avatar_html}</div>
            <div>
              <h1 class="hero-title">{active_cfg["title"]}</h1>
              <p class="hero-sub">{active_cfg["subtitle"]}</p>
            </div>
          </div>
          <div class="hero-quote">{active_cfg["quote"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.nav_page == "Phone Remote":
        local_ip = get_local_ip()
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown("### 📱 Control JIYA & KILL From Your Phone (Same Wi-Fi)")
        st.write(
            "Aap apne mobile phone ke browser se is app ko directly control kar sakte hain, "
            "aur phone ke mic se bol kar commands bhi chala sakte hain:"
        )
        st.code(f"http://{local_ip}:8501", language="text")
        st.info(
            "**Phone se connect karne ke 2 aasaan steps:**\n"
            "1. Apne Phone aur Windows 10 PC ko **ek hi Wi-Fi / Mobile Hotspot** se connect karein.\n"
            f"2. Phone ke Chrome/Safari browser mein **`http://{local_ip}:8501`** type karke kholein — poora dashboard aur Mic/Speaker controls aapke phone par khul jayenge!"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.nav_page == "Advanced Tools":
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown("### 🛠️ Advanced Smart Tools & PC Controller")
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            if st.button("📝 Open Notepad", use_container_width=True) and os.name == "nt":
                subprocess.Popen(["notepad.exe"])
                st.toast("Notepad opened on PC!")
        with t2:
            if st.button("🧮 Open Calculator", use_container_width=True) and os.name == "nt":
                subprocess.Popen(["calc.exe"])
                st.toast("Calculator opened on PC!")
        with t3:
            if st.button("▶️ Open YouTube", use_container_width=True) and os.name == "nt":
                os.startfile("https://www.youtube.com")
        with t4:
            if st.button("📚 CDS Study Prompt", use_container_width=True):
                st.session_state.messages.append(
                    {"role": "user", "content": "Give me a crisp 5-point daily CDS exam revision plan in Hinglish.", "time": datetime.now().strftime("%I:%M %p")}
                )
                ans, used = get_reply("Give me a crisp 5-point daily CDS exam revision plan in Hinglish.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": ans, "time": datetime.now().strftime("%I:%M %p"), "engine": used}
                )
                st.session_state.speak_text = ans
                st.session_state.speak_nonce += 1
                st.session_state.nav_page = "Home"
                st.rerun()

        st.markdown("#### 📌 Saved Quick Notes (Voice se bhi save kar sakte hain: `Note: ...`)")
        new_note = st.text_input("Add a quick note or reminder:")
        if st.button("➕ Save Note") and new_note.strip():
            st.session_state.notes.append(
                {"time": datetime.now().strftime("%d %b, %I:%M %p"), "text": new_note.strip()}
            )
            save_json(NOTES_FILE, st.session_state.notes)
            st.rerun()
        for idx, n in enumerate(reversed(st.session_state.notes), 1):
            st.write(f"**{idx}.** {n['text']} *({n['time']})*")
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.nav_page == "History":
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown("### 📜 Conversation History")
        if not st.session_state.messages:
            st.info("Abhi is session mein koi chat nahi hui hai.")
        else:
            for idx, m in enumerate(st.session_state.messages, 1):
                st.write(f"**{idx}. {m['role'].title()}** ({m.get('time', '')}): {m['content']}")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        ai_avatar = "💗" if is_girl else "⚡"
        if not st.session_state.messages:
            welcome_msg = (
                "Haanji! Main **JIYA** hoon 💗 — bilkul fresh chat shuru ho gayi hai. Bataiye na, aaj main aapki kya madad kar sakti hoon?"
                if is_girl
                else "Hey bhai! Main **KILL** hoon ⚡ — fresh session ready hai. Batao aaj ka kya target hai, mil kar complete karte hain!"
            )
            with st.chat_message("assistant", avatar=ai_avatar):
                st.markdown(welcome_msg)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar=ai_avatar if msg["role"] == "assistant" else "🙂"):
                st.markdown(msg["content"])
                meta = " · ".join(filter(None, [msg.get("time", ""), msg.get("engine", "")]))
                if meta:
                    st.caption(meta)

        if prefs["mic_on"]:
            mic_html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; padding: 9px 14px; border-radius: 16px; background: #0f172a; border: 2px solid {accent}; color: #ffffff; display: flex; align-items: center; gap: 10px;">
              <button id="startRecBtn" style="padding: 7px 14px; border-radius: 10px; border: none; background: {accent}; color: #fff; font-weight: 700; cursor: pointer;">
                🎙️ Tap & Speak
              </button>
              <button id="stopRecBtn" style="padding: 7px 12px; border-radius: 10px; border: 1px solid #94a3b8; background: transparent; color: #fff; cursor: pointer;">
                ⏹ Stop
              </button>
              <span id="micLiveText" style="font-size: 13px;">Mic ON hai — 'Tap & Speak' dabakar Hindi/Hinglish mein bolein...</span>
            </div>
            <script>
              const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
              const statusSpan = document.getElementById('micLiveText');
              let recognition = null;
              if (!SpeechRec) {{
                statusSpan.textContent = "⚠️ Browser speech recognition unsupported. Microsoft Edge ya Chrome use karein.";
              }} else {{
                recognition = new SpeechRec();
                recognition.lang = {json.dumps(prefs['voice_lang'])};
                recognition.interimResults = true;
                recognition.onstart = () => statusSpan.textContent = "🎧 Sun raha hoon... Ab bolein!";
                recognition.onresult = (e) => {{
                  let txt = "";
                  for (let i = e.resultIndex; i < e.results.length; i++) txt += e.results[i][0].transcript;
                  statusSpan.textContent = "🗣️ " + txt;
                  if (e.results[e.results.length - 1].isFinal) {{
                    const parentDoc = window.parent.document;
                    const chatInput = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (chatInput) {{
                      const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value").set;
                      setter.call(chatInput, txt);
                      chatInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
                      setTimeout(() => {{
                        const btn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (btn) btn.click();
                      }}, 150);
                    }}
                  }}
                }};
                recognition.onerror = (e) => statusSpan.textContent = "⚠️ Mic error: " + e.error;
              }}
              document.getElementById('startRecBtn').onclick = () => {{ if (recognition) try {{ recognition.start(); }} catch(e) {{}} }};
              document.getElementById('stopRecBtn').onclick = () => {{ if (recognition) try {{ recognition.stop(); }} catch(e) {{}} }};
            </script>
            """
            components.html(mic_html, height=64)

        prompt = st.chat_input(f"Message {active_cfg['ai_name']} (Hindi / Hinglish / English)…")
        if prompt:
            now_str = datetime.now().strftime("%I:%M %p")
            st.session_state.messages.append({"role": "user", "content": prompt, "time": now_str})
            with st.spinner(f"{active_cfg['ai_name']} is thinking…"):
                ans, used = get_reply(prompt)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": ans,
                    "time": datetime.now().strftime("%I:%M %p"),
                    "engine": used,
                }
            )
            st.session_state.speak_text = ans
            st.session_state.speak_nonce += 1
            st.rerun()
