JIYA PERSONAL AI — STARTER
==========================

1) Python 3.12 install hone ke baad project folder mein CMD kholo.
2) Dependencies install:
   "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt

3) Ollama install karo: https://ollama.com/download
   Phir CMD mein lightweight model download:
   ollama pull llama3.2:3b
   (Download ke liye internet chahiye; baad mein local run ho sakta hai.)

4) App start:
   "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py

5) Browser mein Streamlit ka local address khulega.

MODES
- OFFLINE: Ollama local model; Ollama app/service chalna chahiye aur model downloaded ho.
- ONLINE: Gemini API key sidebar mein enter karo.
- AUTO: pehle Gemini try karega; failure par Ollama fallback karega.

Gemini key: Google AI Studio se apni key lo. Key ko kisi ke saath share mat karo.
App key ko file mein save nahi karta; sidebar/session mein use hoti hai.

Troubleshooting:
- `streamlit` not found: requirements install command dobara chalao.
- Ollama connection failed: Ollama app open/check karo; `ollama list` se models dekho.
- Model missing: `ollama pull llama3.2:3b`
- Error aaye to poora error text/screenshot share karo.

Note: Ye starter template hai; actual working depends on your PC setup, installed packages, Ollama/model, and optional Gemini key.
