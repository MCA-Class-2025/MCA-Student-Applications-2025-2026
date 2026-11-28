# 🍽️ PlatePal — AI Food & Nutrition Assistant

An AI chatbot built with **Google Gemini (free tier)** that:

- 📷 **Recognizes food from a photo** — dish name, cuisine, ingredients, estimated calories & macros (image captioning / vision)
- 💬 **Chats about it** — ask follow-up nutrition/recipe/diet questions, with memory of the conversation
- 🎙️ **Understands your voice** — Speech-to-Text via Gemini's built-in audio understanding (no extra binaries needed)
- 🔊 **Talks back on demand** — Text-to-Speech via gTTS; the reply audio is ready to play, but never autoplays — you press play only when you want to hear it
- 🌐 **Multi-language** — pick a response language in the sidebar; the food analysis, chat replies, and voice output all switch to it

All AI reasoning (vision + chat + speech) runs on a Gemini Flash model,
picked from a **dropdown in the sidebar** so you can switch to a different
model instantly if you hit a free-tier rate limit (each model has its own
separate quota):

- `gemini-3.5-flash-lite` (default — fastest, highest free quota)
- `gemini-3.6-flash`
- `gemini-3.5-flash`
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`

---

## 1. Prerequisites

- Python 3.10+ installed
- VS Code with the **Python extension**
- A free Gemini API key from **https://aistudio.google.com/apikey**
- A microphone (for voice input) — the browser will ask permission the first time

## 2. Setup (in VS Code)

Open the project folder in VS Code, then open a terminal (``Ctrl+` ``) and run:

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env      # Windows: copy .env.example .env
# then open .env and paste your key after GEMINI_API_KEY=
```

> You can also skip the `.env` file and just paste the key into the app's
> sidebar text box at runtime — either way works.

## 3. Run it

```bash
streamlit run app.py
```

This opens the app at `http://localhost:8501` in your browser.

## 4. How to use

1. Enter your Gemini API key in the sidebar (if not already set in `.env`).
2. Upload a photo of food and click **Analyze Food** — you'll get the dish
   name, likely ingredients, estimated calories, and macros.
3. Ask follow-up questions either by:
   - Typing in the chat box, or
   - Clicking the microphone (**Record a voice message**) and speaking
4. Toggle **🔊 Speak responses** in the sidebar to have answers read aloud.

## Project structure

```
PlatePal/
├── app.py                  # Streamlit UI + orchestration
├── utils/
│   ├── gemini_utils.py     # Gemini vision + chat calls
│   └── speech_utils.py     # Text-to-Speech (gTTS)
├── requirements.txt
├── .env.example
└── README.md
```

## Notes on the "free tier" services used

| Feature          | Service                              | Notes                                   |
|-------------------|---------------------------------------|------------------------------------------|
| Image captioning  | Gemini `gemini-3.5-flash-lite` (vision)   | Free tier: generous requests/day, fast   |
| Chat              | Gemini `gemini-3.5-flash-lite` (text)     | Same model reused, no extra key needed   |
| Speech-to-Text    | Gemini `gemini-3.5-flash-lite` (audio input)| Free tier, no extra binaries/keys needed |
| Text-to-Speech    | `gTTS`                               | Free, no API key, needs internet         |

If you get a `429` error mentioning `limit: 20` (or similar), that's a real
free-tier rate limit — just pick a different model from the sidebar dropdown
and try again, since each model has its own separate quota. If instead you
see `limit: 0` or a `404 "no longer available"`, that specific model ID has
been retired by Google — check https://ai.google.dev/gemini-api/docs/models
for current model names and update `MODEL_OPTIONS` in
`utils/gemini_utils.py`.

## Troubleshooting

- **"Enter your free Gemini API key"** — get one at https://aistudio.google.com/apikey (Google account required, no credit card).
- **Microphone button doesn't appear** — requires Streamlit ≥ 1.38 (already pinned in `requirements.txt`); make sure you `pip install -r requirements.txt` inside your venv.
- **STT returns nothing** — speak clearly, keep clips short (<20s), and make sure you have an internet connection (the free Google Web Speech API needs one).
- **No sound plays** — check your browser didn't block autoplay; you can also just click the audio player that appears under the response.
