"""
PlatePal — AI Food & Nutrition Assistant  (Submission Build)
Run with:  streamlit run app.py
"""

import os, re, html as _html
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
import streamlit as st

from utils.gemini_utils import (
    configure_gemini, analyze_food_image, chat_with_gemini,
    transcribe_audio, set_model, MODEL_OPTIONS,
)
from utils.speech_utils import text_to_speech_bytes
from utils.history_utils import load_history, save_conversation, delete_conversation
from utils.rag_utils import (
    add_to_vector_store, retrieve_similar,
    build_rag_context, get_store_stats, clear_vector_store,
)
from utils.csv_utils import build_export_csv
from utils.xlsx_utils import build_export_xlsx
from utils.food_apis import (
    get_recipes, get_weather_food_advice,
    get_cultural_info, get_exchange_rates, lookup_product,
    _estimate_cost,
)

load_dotenv()

APP_NAME    = "PlatePal"
APP_TAGLINE = "Snap a photo, ask a question — get nutrition insight in your language, by text or voice."

st.set_page_config(page_title=APP_NAME, page_icon="🍽️", layout="wide")

# ── Language table ────────────────────────────────────────────────
LANGUAGES = {
    "English":                  ("English",            "en",    None,                   "'DM Sans',sans-serif"),
    "Hindi (हिन्दी)":           ("Hindi",              "hi",    "Noto+Sans+Devanagari", "'Noto Sans Devanagari',sans-serif"),
    "Marathi (मराठी)":          ("Marathi",            "mr",    "Noto+Sans+Devanagari", "'Noto Sans Devanagari',sans-serif"),
    "Tamil (தமிழ்)":            ("Tamil",              "ta",    "Noto+Sans+Tamil",      "'Noto Sans Tamil',sans-serif"),
    "Telugu (తెలుగు)":          ("Telugu",             "te",    "Noto+Sans+Telugu",     "'Noto Sans Telugu',sans-serif"),
    "Bengali (বাংলা)":          ("Bengali",            "bn",    "Noto+Sans+Bengali",    "'Noto Sans Bengali',sans-serif"),
    "Kannada (ಕನ್ನಡ)":          ("Kannada",            "kn",    "Noto+Sans+Kannada",    "'Noto Sans Kannada',sans-serif"),
    "Gujarati (ગુજરાતી)":       ("Gujarati",           "gu",    "Noto+Sans+Gujarati",   "'Noto Sans Gujarati',sans-serif"),
    "Arabic (العربية)":         ("Arabic",             "ar",    "Noto+Kufi+Arabic",     "'Noto Kufi Arabic',sans-serif"),
    "Japanese (日本語)":         ("Japanese",           "ja",    "Noto+Sans+JP",         "'Noto Sans JP',sans-serif"),
    "Chinese Simplified (中文)": ("Chinese Simplified", "zh-CN", "Noto+Sans+SC",         "'Noto Sans SC',sans-serif"),
    "Spanish (Español)":        ("Spanish",            "es",    None,                   "'DM Sans',sans-serif"),
    "French (Français)":        ("French",             "fr",    None,                   "'DM Sans',sans-serif"),
    "German (Deutsch)":         ("German",             "de",    None,                   "'DM Sans',sans-serif"),
    "Portuguese (Português)":   ("Portuguese",         "pt",    None,                   "'DM Sans',sans-serif"),
    "Russian (Русский)":        ("Russian",            "ru",    None,                   "'DM Sans',sans-serif"),
}

# ── Helpers ───────────────────────────────────────────────────────
def extract_dish_name(text):
    if not text: return ""
    m = re.search(r"\*\*[^*]*:?\*\*\s*(.+)", text)
    return m.group(1).split("\n")[0].strip()[:60] if m else ""

def render_ticket(raw_text, font_family="'DM Sans',sans-serif"):
    pattern = re.compile(r"\*\*([^*]+?):?\*\*\s*(.*?)(?=\*\*[^*]+?:?\*\*|$)", re.DOTALL)
    fields = [(l.strip(), v.strip().strip("*").strip())
              for l, v in pattern.findall(raw_text or "") if l.strip() and v.strip()]
    if not fields:
        st.markdown(raw_text); return
    dish = _html.escape(fields[0][1])
    rows = "".join(
        f'<div class="pp-ticket-row">'
        f'<span class="pp-ticket-label" style="font-family:{font_family}">{_html.escape(l)}</span>'
        f'<span class="pp-ticket-dots"></span>'
        f'<span class="pp-ticket-value{"  pp-mono" if any(c.isdigit() for c in v) else ""}" '
        f'style="font-family:{font_family}">{_html.escape(v)}</span>'
        f'</div>'
        for l, v in fields
    )
    st.markdown(
        f'<div class="pp-ticket">'
        f'<div class="pp-ticket-header">✦ {dish} ✦</div>{rows}'
        f'<div class="pp-ticket-footer">★ &nbsp; PlatePal Kitchen &nbsp; ★</div></div>',
        unsafe_allow_html=True)

DISH_COST_INR = {
    "samosa":20,"biryani":180,"paneer":150,"masala":200,"dosa":60,
    "idli":40,"curry":150,"naan":40,"roti":15,"pizza":250,"pasta":200,
    "burger":150,"sushi":400,"ramen":200,"tacos":120,"gulab jamun":30,
    "halwa":50,"kheer":60,"ice cream":80,"poha":50,"pakora":60,
}

def _estimate_cost_or_default(dish_name: str) -> int:
    dl = dish_name.lower()
    for k, v in DISH_COST_INR.items():
        if k in dl:
            return v
    return 150

HERO = (f'<div class="pp-hero"><div class="pp-hero-checks"></div>'
        f'<div class="pp-hero-body"><div class="pp-hero-icon">🍔</div>'
        f'<div class="pp-hero-text"><h1>{APP_NAME}</h1><p>{APP_TAGLINE}</p></div></div>'
        f'<div class="pp-hero-checks-bt"></div></div>')

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=DM+Sans:wght@400;500;600&family=Courier+Prime:wght@400;700&display=swap');
:root{--parch:#FDF3DC;--parch2:#F5E6C0;--cherry:#B83227;--cherry-dk:#8C2218;--must:#D4891A;--must-lt:#F0B84B;--ink:#2A1206;--ink-s:#6B4226;--card:#FFFBF0;--bdr:#D4B483;--bdr-dk:#A07840;}
.stApp{background:var(--parch);}
.stApp,p,span,label,div{font-family:'DM Sans',sans-serif;color:var(--ink);}
section[data-testid="stSidebar"]{background:var(--card);border-right:3px solid var(--bdr-dk);}
.pp-hero{background:var(--cherry);border-radius:12px;padding:0;margin-bottom:24px;overflow:hidden;box-shadow:0 4px 0 var(--cherry-dk),0 6px 16px rgba(42,18,6,.22);}
.pp-hero-checks{height:14px;background:repeating-linear-gradient(90deg,#fff 0,#fff 14px,var(--must) 14px,var(--must) 28px);}
.pp-hero-checks-bt{height:14px;background:repeating-linear-gradient(90deg,var(--must) 0,var(--must) 14px,#fff 14px,#fff 28px);}
.pp-hero-body{padding:20px 28px 22px;display:flex;align-items:center;gap:18px;}
.pp-hero-icon{font-size:3rem;line-height:1;}
.pp-hero-text h1{font-family:'Playfair Display',serif;font-weight:900;font-style:italic;margin:0;font-size:2.3rem;color:#FFF8E7;text-shadow:2px 2px 0 var(--cherry-dk);line-height:1.1;}
.pp-hero-text p{margin:6px 0 0;color:rgba(255,248,231,.85);font-size:.95rem;font-family:'Courier Prime',monospace;}
div[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card)!important;border:2px solid var(--bdr)!important;border-radius:10px!important;box-shadow:3px 3px 0 var(--bdr-dk)!important;}

/* Chat bubble — keep overflow hidden so avatar text can't escape */
div[data-testid="stChatMessage"]{background:var(--parch2)!important;border-radius:8px!important;border:1px solid var(--bdr)!important;overflow:hidden!important;}

/* Avatar circles — clip and colour them; font-size:0 hides icon text inside */
div[data-testid="stChatMessage"] > div:first-child {
    overflow:hidden!important; width:34px!important; min-width:34px!important;
    height:34px!important; border-radius:50%!important;
    background:var(--cherry)!important; font-size:0!important;
    color:transparent!important; flex-shrink:0!important;
}
/* Make user avatar mustard */
div[data-testid="stChatMessage"][data-testid*="user"] > div:first-child,
div[data-testid="stChatMessage"].st-emotion-cache-user > div:first-child {
    background:var(--must)!important;
}

/* Kill ALL material-icon text globally — font-size 0 collapses text but keeps layout */
.material-icons,.material-icons-round,.material-icons-outlined,
.material-symbols-rounded,.material-symbols-outlined{
    font-size:0!important; width:0!important; overflow:hidden!important;
    display:inline-block!important; vertical-align:middle!important;
}

/* Expander header — hide the leaking arrow text */
details > summary { list-style: none !important; }
details > summary::-webkit-details-marker { display: none !important; }
[data-testid="stExpanderToggleIcon"] { display:none!important; }

.stButton>button{border-radius:6px;font-family:'DM Sans',sans-serif;font-weight:600;background:var(--card);border:2px solid var(--bdr-dk);color:var(--ink);transition:all .12s;}
.stButton>button:hover{background:var(--parch2);border-color:var(--must);color:var(--must);transform:translateY(-1px);}
.stButton>button[kind="primary"]{background:var(--cherry);border:2px solid var(--cherry-dk);color:#FFF8E7;box-shadow:2px 2px 0 var(--cherry-dk);}
.stButton>button[kind="primary"]:hover{background:var(--cherry-dk);transform:translateY(-1px);}
.pp-section-title{font-family:'Playfair Display',serif;font-weight:700;font-size:1.15rem;margin-bottom:6px;color:var(--cherry);}
.pp-badge{display:inline-block;font-family:'Courier Prime',monospace;letter-spacing:.12em;text-transform:uppercase;background:var(--must-lt);color:var(--ink);border:1px solid var(--must);border-radius:4px;padding:2px 10px;font-size:.72rem;font-weight:700;margin-bottom:10px;}
.pp-history-item{background:var(--parch2);border:1px solid var(--bdr);border-radius:8px;padding:10px 12px;margin-bottom:10px;}
.pp-history-item b{font-size:.95rem;} .pp-history-item small{font-size:.78rem;color:var(--ink-s);}
section[data-testid="stFileUploaderDropzone"],div[data-testid="stAudioInput"]{border-radius:8px!important;border:2px dashed var(--bdr-dk)!important;background:var(--parch2)!important;}
.pp-ticket{background:#FFFDF5;border:2px solid var(--bdr-dk);border-radius:4px;padding:16px 20px;margin-top:8px;box-shadow:2px 2px 0 var(--bdr);font-family:'Courier Prime',monospace;}
.pp-ticket-header{text-align:center;font-family:'Playfair Display',serif;font-weight:700;font-size:1rem;color:var(--cherry);letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid var(--bdr);padding-bottom:8px;margin-bottom:10px;}
.pp-ticket-row{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px dotted var(--bdr);}
.pp-ticket-row:last-child{border-bottom:none;}
.pp-ticket-label{font-family:'Courier Prime',monospace;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-s);min-width:28%;max-width:32%;}
.pp-ticket-dots{flex:1;border-bottom:1px dotted var(--bdr);margin:0 6px 4px;min-width:10px;}
.pp-ticket-value{font-family:'Courier Prime',monospace;color:var(--ink);text-align:right;font-size:.88rem;max-width:62%;word-break:break-word;}
.pp-ticket-value.pp-mono{color:var(--cherry);font-weight:700;}
.pp-ticket-footer{text-align:center;font-family:'Courier Prime',monospace;font-size:.7rem;color:var(--bdr-dk);letter-spacing:.08em;margin-top:10px;padding-top:8px;border-top:1px solid var(--bdr);}
hr{border-color:var(--bdr)!important;margin:12px 0!important;}
</style>

<!-- JS: wipe raw material-icon text nodes from the DOM immediately and on every mutation -->
<script>
(function(){
  const BAD = new Set(["smart_toy","arrow_right","arrow_drop_down","arrow_drop_up",
    "expand_more","expand_less","chevron_right","chevron_left","close","send",
    "mic","upload_file","download","delete","save","check","info","menu","search"]);
  function clean(root){
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const hits = [];
    let n;
    while((n = tw.nextNode())) {
      const t = n.nodeValue.trim();
      if(BAD.has(t) || /^_[a-z_]{3,}$/.test(t)) hits.push(n);
    }
    hits.forEach(n => { n.nodeValue = ""; });
  }
  function runAll(){
    clean(document.body);
    try{ clean(window.parent.document.body); }catch(e){}
  }
  runAll();
  const ob = new MutationObserver(runAll);
  ob.observe(document.body,{childList:true,subtree:true});
  try{ ob.observe(window.parent.document.body,{childList:true,subtree:true}); }catch(e){}
})();
</script>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────
st.sidebar.markdown(f"### ⚙️ {APP_NAME} Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key", value=os.getenv("GEMINI_API_KEY",""),
    type="password", help="Free: https://aistudio.google.com/apikey")

if not api_key:
    st.markdown(HERO, unsafe_allow_html=True)
    st.warning("👈 Enter your free Gemini API key in the sidebar.")
    st.info("Get one free at https://aistudio.google.com/apikey")
    st.stop()

configure_gemini(api_key)

model_choice = st.sidebar.selectbox("🤖 Gemini model", MODEL_OPTIONS, index=0,
    help="Switch if you hit a 429 rate-limit — each model has its own free quota.")
set_model(model_choice)

language_label = st.sidebar.selectbox("🌐 Response language", list(LANGUAGES.keys()), index=0)
language_name, tts_lang_code, gfont_param, font_family = LANGUAGES[language_label]

# Inject language font
if gfont_param:
    st.markdown(
        f'<link href="https://fonts.googleapis.com/css2?family={gfont_param}:wght@400;600&display=swap" rel="stylesheet">'
        f'<style>.stApp p,.stApp div,.stApp span,.stApp label,'
        f'div[data-testid="stChatMessage"] *,'
        f'div[data-testid="stMarkdownContainer"] *,'
        f'.pp-ticket,.pp-ticket *,'
        f'textarea,input[type="text"]{{font-family:{font_family}!important;}}</style>',
        unsafe_allow_html=True)

voice_reply = st.sidebar.checkbox("🔊 Prepare voice reply (click to play)", value=True)
st.sidebar.markdown("---")

# ── Session state ─────────────────────────────────────────────────
for k,v in {"messages":[],"food_context":"","last_audio_hash":None,
            "pending_audio":None,"uploader_key":0,"last_analysis":None,
            "stored_image":None,"last_language":language_name,
            "retranslating":False,
            "rag_context":"",
            "api_results":{},
            "last_image_info":{},
        }.items():
    if k not in st.session_state: st.session_state[k] = v

def reset_conversation(also_save=True):
    if also_save and st.session_state.messages:
        dish = extract_dish_name(
            st.session_state.last_analysis["raw_text"] if st.session_state.last_analysis else "")
        save_conversation(st.session_state.messages, st.session_state.food_context, dish)
    st.session_state.update({"messages":[],"food_context":"","last_analysis":None,
                              "pending_audio":None,"stored_image":None})
    st.session_state.uploader_key += 1

# ── Auto-retranslate when language changes ────────────────────────
lang_changed = (language_name != st.session_state.last_language)
st.session_state.last_language = language_name

if lang_changed and st.session_state.stored_image is not None:
    with st.spinner(f"🌐 Retranslating into {language_name}..."):
        try:
            result = analyze_food_image(st.session_state.stored_image, language=language_name)
            st.session_state.food_context  = result["raw_text"]
            st.session_state.last_analysis = result
            # Replace first assistant message (old analysis) with new translation
            msgs = st.session_state.messages
            if msgs and msgs[0]["role"] == "assistant":
                msgs[0] = {"role":"assistant","content":result["raw_text"]}
            else:
                msgs.insert(0,{"role":"assistant","content":result["raw_text"]})
        except RuntimeError as e:
            st.sidebar.warning("⏳ Rate limit — try switching models." if "429" in str(e)
                               else f"Retranslation error: {e}")
    st.rerun()

# ── Sidebar: Save / Clear / History ──────────────────────────────
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("💾 Save", use_container_width=True,
                 disabled=not bool(st.session_state.messages)):
        dish = extract_dish_name(
            st.session_state.last_analysis["raw_text"] if st.session_state.last_analysis else "")
        if save_conversation(st.session_state.messages, st.session_state.food_context, dish):
            st.sidebar.success("Saved!")
with c2:
    if st.button("🗑️ Clear", use_container_width=True):
        reset_conversation(also_save=True); st.rerun()

history = load_history()
with st.sidebar.expander(f"Saved Conversations ({len(history)})", expanded=False):
    if not history:
        st.caption("No saved conversations yet.")
    for entry in history:
        st.markdown(
            f'<div class="pp-history-item">'
            f'<b>{_html.escape(entry.get("dish") or "Conversation")}</b><br>'
            f'<small>{entry.get("timestamp","")} · {len(entry.get("messages",[]))} messages</small>'
            f'</div>', unsafe_allow_html=True)
        lc, dc = st.columns(2)
        with lc:
            if st.button("Load", key=f"load_{entry['id']}", use_container_width=True):
                st.session_state.messages      = entry.get("messages",[])
                st.session_state.food_context  = entry.get("food_context","")
                st.session_state.last_analysis = (
                    {"raw_text":entry["food_context"]} if entry.get("food_context") else None)
                st.session_state.pending_audio = None
                st.session_state.stored_image  = None
                st.session_state.uploader_key += 1
                st.rerun()
        with dc:
            if st.button("Delete", key=f"del_{entry['id']}", use_container_width=True):
                delete_conversation(entry["id"]); st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Model: `{model_choice}` · TTS: gTTS")

# ── Main layout ───────────────────────────────────────────────────
st.markdown(HERO, unsafe_allow_html=True)
col1, col2 = st.columns([1, 1.4])

# Column 1 — Upload + Analysis
with col1:
    with st.container(border=True):
        st.markdown('<div class="pp-badge">STEP 1</div>', unsafe_allow_html=True)
        st.markdown('<div class="pp-section-title">📷 Upload a food photo</div>', unsafe_allow_html=True)

        img_file = st.file_uploader(
            "img", type=["jpg","jpeg","png","webp"],
            label_visibility="collapsed",
            key=f"food_image_{st.session_state.uploader_key}")

        # Keep image visible across reruns
        if img_file:
            image = Image.open(img_file).convert("RGB")
            st.session_state.stored_image = image
        else:
            image = st.session_state.stored_image

        if image is not None:
            st.image(image, use_container_width=True)
            if st.button("🔍 Analyze Food", type="primary", use_container_width=True):
                with st.spinner("Analyzing with Gemini..."):
                    try:
                        result = analyze_food_image(image, language=language_name)
                    except Exception as e:
                        result = None
                        err = str(e).lower()
                        if "429" in str(e):
                            st.error("⏳ Rate limit — try another model in the sidebar.")
                        elif "timed out" in err or "timeout" in err:
                            st.error("⏳ Request timed out — try again (image was compressed, should be faster now).")
                        else:
                            st.error(f"Error: {e}")
                if result:
                    st.session_state.food_context  = result["raw_text"]
                    st.session_state.last_analysis = result
                    st.session_state.messages.append({"role":"assistant","content":result["raw_text"]})
                    # Store image metadata for CSV export
                    if image is not None:
                        w, h = image.size
                        st.session_state.last_image_info = {
                            "filename":   getattr(img_file, "name", "uploaded_image"),
                            "dimensions": f"{w}x{h}px",
                            "size_kb":    round(len(img_file.getvalue()) / 1024, 1) if img_file else "—",
                        }
                    # Add to RAG vector store (background, non-blocking)
                    dish = extract_dish_name(result["raw_text"])
                    add_to_vector_store(dish, result["raw_text"], api_key,
                                        extra_metadata={"language": language_name, "model": model_choice})
                    st.rerun()

        if st.session_state.last_analysis:
            st.markdown("---")
            st.markdown('<div class="pp-section-title">🥗 Analysis</div>', unsafe_allow_html=True)
            render_ticket(st.session_state.last_analysis["raw_text"], font_family=font_family)

# Column 2 — Chat
with col2:
    with st.container(border=True):
        st.markdown('<div class="pp-badge">STEP 2</div>', unsafe_allow_html=True)
        st.markdown('<div class="pp-section-title">💬 Chat about your food</div>', unsafe_allow_html=True)

        chat_box = st.container(height=330)
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if st.session_state.pending_audio:
            st.caption("🔊 Voice reply ready — press ▶ to hear it")
            st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=False)
            st.session_state.pending_audio = None

        st.divider()
        st.markdown("**🎙️ Speak your question**")
        audio_value = st.audio_input("mic", label_visibility="collapsed")

        user_input = None
        if audio_value is not None:
            ab   = audio_value.getvalue()
            ahsh = hash(ab)
            if ahsh != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = ahsh
                with st.spinner("Transcribing..."):
                    try:    voice_text = transcribe_audio(ab)
                    except Exception as e:
                        voice_text = ""
                        st.error("⏳ Rate limit — try another model." if "429" in str(e) else f"Error: {e}")
                if voice_text:
                    st.success(f"Heard: {voice_text}")
                    user_input = voice_text
                else:
                    st.warning("Couldn't understand audio — try typing instead.")

        typed = st.chat_input("Type your question about the food...")
        if typed: user_input = typed

        if user_input:
            st.session_state.messages.append({"role":"user","content":user_input})
            with st.spinner("Thinking..."):
                try:
                    # RAG: retrieve similar past food analyses to enrich the answer
                    similar = retrieve_similar(user_input, api_key, top_k=3)
                    rag_ctx = build_rag_context(similar)
                    st.session_state.rag_context = rag_ctx

                    # Combine food context + RAG context
                    full_context = st.session_state.food_context
                    if rag_ctx:
                        full_context = full_context + "\n\n" + rag_ctx

                    reply = chat_with_gemini(
                        user_input, history=st.session_state.messages,
                        food_context=full_context, language=language_name)
                except RuntimeError as e:
                    reply = ("⏳ Rate limit — switch models in sidebar."
                             if "429" in str(e) else f"⚠️ Error: {e}")
            st.session_state.messages.append({"role":"assistant","content":reply})
            if voice_reply:
                with st.spinner("Preparing voice reply..."):
                    try: st.session_state.pending_audio = text_to_speech_bytes(reply, lang=tts_lang_code)
                    except Exception as e: st.warning(f"Voice unavailable: {e}")
            st.rerun()


# ─────────────────────────────────────────────────────────────────
# API Features Panel (shown after a food is analyzed)
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# Live API Features Panel
# ─────────────────────────────────────────────────────────────────
if st.session_state.last_analysis:
    dish_name = extract_dish_name(st.session_state.last_analysis.get("raw_text", "")) or "food"

    st.markdown("---")
    st.markdown(
        f'<div class="pp-section-title">🌐 Live API Features for "{dish_name}"</div>',
        unsafe_allow_html=True)
    st.caption("5 external APIs adding unique context: recipes, weather match, cultural origin, currency & barcode lookup.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🍳 Recipes",
        "🌤️ Weather Match",
        "🌍 Cultural Origin",
        "💰 Price in Currencies",
        "🔍 Product Search",
    ])

    # ── Tab 1: TheMealDB Recipes ──────────────────────────────────
    with tab1:
        st.markdown("**TheMealDB** — free recipe database with step-by-step instructions. No API key needed.")
        with st.spinner("Searching TheMealDB..."):
            recipes = get_recipes(dish_name)
        st.session_state.api_results["recipes"] = recipes
        if not recipes["ok"]:
            st.error(f"TheMealDB error: {recipes['error']}")
        elif not recipes["recipes"]:
            st.info(f"No TheMealDB recipes for '{dish_name}'. This API works best with common international dishes — try Pizza, Chicken Curry, or Biryani.")
        else:
            for r in recipes["recipes"]:
                with st.expander(f"🍽️ {r['name']}  ·  {r['area']} · {r['category']}", expanded=True):
                    col_a, col_b = st.columns([1, 2])
                    with col_a:
                        if r["thumbnail"]:
                            st.image(r["thumbnail"], use_container_width=True)
                        if r["youtube"]:
                            st.markdown(f"[▶️ Watch on YouTube]({r['youtube']})")
                    with col_b:
                        if r["tags"]:
                            st.caption(f"Tags: {r['tags']}")
                        if r["ingredients"]:
                            st.markdown("**Ingredients:**")
                            st.markdown("  \n".join([f"• {i}" for i in r["ingredients"][:10]]))
                    if r["instructions"]:
                        st.markdown("**Instructions:**")
                        st.markdown(r["instructions"])

    # ── Tab 2: OpenWeatherMap ─────────────────────────────────────
    with tab2:
        st.markdown("**OpenWeatherMap** — live weather in your city + whether this dish suits today's conditions. Needs `OPENWEATHER_API_KEY` in `.env`.")
        city_input = st.text_input("Your city:", value="Mumbai", key="weather_city")
        if st.button("🌤️ Check Weather Match", type="primary"):
            with st.spinner(f"Fetching weather for {city_input}..."):
                wx = get_weather_food_advice(dish_name, city=city_input)
            st.session_state.api_results["weather"] = wx
            if not wx["ok"]:
                st.warning(f"Weather error: {wx['error']}")
                st.info("Get a free key at https://openweathermap.org/api → add `OPENWEATHER_API_KEY=your_key` to `.env`.")
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🌡️ Temp", f"{wx['temp_c']}°C")
                c2.metric("🤔 Feels", f"{wx['feels_c']}°C")
                c3.metric("💧 Humidity", f"{wx['humidity']}%")
                c4.metric("💨 Wind", f"{wx['wind_kmh']} km/h")
                st.markdown(f"**{wx['city']}, {wx['country']}:** {wx['condition']}")
                st.success(wx["advice"])
        else:
            st.info("Enter your city and click the button to get a live weather-based food suggestion.")

    # ── Tab 3: Cultural Origin ────────────────────────────────────
    with tab3:
        st.markdown("**Wikipedia + Curated Data** — dish history, cultural origin & cuisine type. No API key needed.")
        with st.spinner("Fetching from Wikipedia..."):
            culture = get_cultural_info(dish_name)
        st.session_state.api_results["culture"] = culture
        if not culture["ok"]:
            st.error(f"Error: {culture['error']}")
        else:
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if culture["wiki"].get("image"):
                    st.image(culture["wiki"]["image"], use_container_width=True)
            with col_b:
                st.markdown(f"### 🌍 {culture['dish']}")
                ca, cb = st.columns(2)
                ca.metric("Origin", culture["origin"])
                cb.metric("Cuisine Type", culture["cuisine_type"])
                if culture["wiki"].get("url"):
                    st.markdown(f"[📖 Read full Wikipedia article ↗]({culture['wiki']['url']})")
            if culture["wiki"].get("extract"):
                st.markdown("---")
                st.markdown(f"**{culture['wiki'].get('title', dish_name)}** — {culture['wiki']['extract']}")

    # ── Tab 4: Price in Currencies ────────────────────────────────
    with tab4:
        st.markdown("**ExchangeRate API** — estimates dish cost in 8 currencies using live rates. Needs `EXCHANGERATE_API_KEY` in `.env`.")
        default_cost = float(_estimate_cost(dish_name))
        base_price = st.number_input("Estimated price in INR (₹):",
            min_value=1.0, value=default_cost, step=10.0, key="price_input")
        if st.button("💰 Convert to World Currencies", type="primary"):
            with st.spinner("Fetching live exchange rates..."):
                fx = get_exchange_rates(dish_name, cost_inr=base_price)
            st.session_state.api_results["exchange_rates"] = fx
            if not fx["ok"]:
                st.warning(f"ExchangeRate error: {fx['error']}")
                st.info("Get free key at https://app.exchangerate-api.com/ → add `EXCHANGERATE_API_KEY=your_key` to `.env`.")
            else:
                st.success(f"**{dish_name}** at ₹{base_price:.0f} converts to:")
                cols = st.columns(4)
                for i, conv in enumerate(fx["conversions"]):
                    cols[i % 4].metric(
                        f"{conv['symbol']} {conv['currency']}",
                        f"{conv['symbol']}{conv['cost']}"
                    )
                st.caption(f"Rates last updated: {fx['last_updated']}")
        else:
            st.info("Adjust the INR price and click Convert to see live exchange rates.")

    # ── Tab 5: Open Food Facts Product Search ────────────────────
    with tab5:
        st.markdown("**Open Food Facts** — search any packaged food product by name. Get Nutri-Score, ingredients & nutrition per 100g. No API key needed.")
        st.caption("Works great with Indian products: Maggi, Britannia, Parle, Amul, Haldirams etc.")
        product_input = st.text_input(
            "Search for a packaged food product:",
            placeholder="e.g. Maggi, Nutella, Parle-G, Amul butter",
            key="product_search_input"
        )
        if st.button("🔍 Search Product", type="primary"):
            if not product_input.strip():
                st.warning("Please enter a product name.")
            else:
                with st.spinner(f"Searching Open Food Facts for '{product_input}'..."):
                    result = lookup_product(product_input)
                st.session_state.api_results["products"] = result
                if not result["ok"]:
                    st.error(f"Search failed: {result['error']}")
                elif not result["products"]:
                    st.info(f"No products found for '{product_input}'. Try a simpler name like 'Maggi' or 'Britannia'.")
                else:
                    for p in result["products"]:
                        with st.expander(f"📦 {p['name']} — {p['brand']}", expanded=True):
                            col_a, col_b = st.columns([1, 2])
                            with col_a:
                                if p["image"]:
                                    st.image(p["image"], use_container_width=True)
                                st.metric("Nutri-Score", p["nutriscore"])
                                st.markdown(f"**Qty:** {p['quantity']}")
                            with col_b:
                                c1, c2, c3 = st.columns(3)
                                c1.metric("Calories/100g", f"{p['calories_100g']} kcal")
                                c2.metric("Protein/100g", f"{p['protein_100g']} g")
                                c3.metric("Carbs/100g", f"{p['carbs_100g']} g")
                                c4, c5, c6 = st.columns(3)
                                c4.metric("Fat/100g", f"{p['fat_100g']} g")
                                c5.metric("Sugars/100g", f"{p['sugars_100g']} g")
                                c6.metric("Salt/100g", f"{p['salt_100g']} g")
                            if p["ingredients"] != "—":
                                with st.expander("📋 Ingredients"):
                                    st.write(p["ingredients"])
        else:
            st.info("Try searching: **Maggi** · **Parle-G** · **Amul Butter** · **Haldirams** · **Britannia** · **Nutella** · **Oreo**")

    # ─────────────────────────────────────────────────────────────
    # RAG Info Panel
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="pp-section-title">🧠 RAG — Retrieval-Augmented Generation</div>',
                unsafe_allow_html=True)

    # Force re-read from disk every render so counter stays current
    rag_stats = get_store_stats()
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Dishes in Vector Store", rag_stats["count"])
    col_r2.metric("Unique Dishes", len(rag_stats["dishes"]))
    col_r3.metric("Last Added", rag_stats["latest"] or "—")

    if rag_stats["dishes"]:
        st.caption("Dishes stored: " + " · ".join(rag_stats["dishes"]))

    if st.session_state.rag_context:
        with st.expander("🔍 RAG Context used in last reply", expanded=True):
            st.text(st.session_state.rag_context)
    else:
        st.info("💡 RAG is active — analyze a second food dish then ask a comparison question to see it retrieve past analyses automatically.")

    # ─────────────────────────────────────────────────────────────
    # Data Export — CSV and Excel
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="pp-section-title">📊 Export All Data</div>',
                unsafe_allow_html=True)
    st.caption("Downloads everything from this session — food photo, analysis, conversation, RAG results, and all API data — as CSV or as a formatted Excel workbook.")

    dish = extract_dish_name(st.session_state.last_analysis.get("raw_text","")) or "food"
    rag_hits = retrieve_similar(dish, api_key, top_k=3) if api_key else []
    base_filename = f"platepal_{dish.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    export_kwargs = dict(
        analysis_text = st.session_state.last_analysis.get("raw_text",""),
        messages      = st.session_state.messages,
        language      = language_name,
        model         = model_choice,
        image_info    = st.session_state.get("last_image_info", {}),
        api_results   = st.session_state.get("api_results", {}),
        rag_results   = rag_hits,
        pil_image     = st.session_state.get("stored_image"),
    )

    csv_bytes  = build_export_csv(**export_kwargs)
    xlsx_bytes = build_export_xlsx(**export_kwargs)

    col_xlsx, col_csv = st.columns(2)
    with col_xlsx:
        st.download_button(
            label     = "📊 Download Excel (.xlsx, formatted, photo embedded)",
            data      = xlsx_bytes,
            file_name = f"{base_filename}.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type      = "primary",
            use_container_width = True,
        )
    with col_csv:
        st.download_button(
            label     = "⬇️ Download CSV (raw, includes Base64 image data)",
            data      = csv_bytes,
            file_name = f"{base_filename}.csv",
            mime      = "text/csv",
            type      = "secondary",
            use_container_width = True,
        )