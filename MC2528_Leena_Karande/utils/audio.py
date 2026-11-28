"""Private browser text-to-speech; no external voice API is used."""

import json
import streamlit.components.v1 as components


def stt_available() -> bool:
    return False


def tts_widget(text: str, lang_code: str = "en-US", key: str = "tts") -> None:
    if not text:
        return
    encoded = json.dumps(text)
    components.html(
        f"""<div style='display:flex;gap:8px;align-items:center'>
        <button id='{key}_play' style='border:0;border-radius:12px;padding:8px 13px;background:#2dd4bf;color:#071622;font-weight:700;cursor:pointer'>🔊 Listen</button>
        <button id='{key}_stop' style='border:1px solid #58627c;border-radius:12px;padding:8px 13px;background:#182035;color:#f8fafc;font-weight:700;cursor:pointer'>⏹ Stop</button>
        <span id='{key}_status' style='color:#b9b6d9;font-size:12px'></span></div><script>
        const play=document.getElementById('{key}_play'), stop=document.getElementById('{key}_stop'), status=document.getElementById('{key}_status');
        play.onclick=()=>{{
          const target='{lang_code}'.toLowerCase(), voices=speechSynthesis.getVoices();
          const voice=voices.find(v=>v.lang.toLowerCase()===target)||voices.find(v=>v.lang.toLowerCase().startsWith(target.split('-')[0]+'-'));
          if(!voice){{status.textContent='No '+target+' voice is installed on this device.'; return;}}
          status.textContent=''; speechSynthesis.cancel(); let u=new SpeechSynthesisUtterance({encoded}); u.lang='{lang_code}'; u.voice=voice; speechSynthesis.speak(u);
        }};
        stop.onclick=()=>speechSynthesis.cancel();
        </script>""",
        height=52,
    )
