"""Optional local LLM bridge. FundFlow works without Ollama.
When Ollama is available, Qwen 2.5 1.5B can turn retrieved finance context into a natural-language answer.
"""
import requests
OLLAMA_URL="http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL="qwen2.5:1.5b"
def available(timeout=0.7):
    try: return requests.get("http://127.0.0.1:11434/api/tags",timeout=timeout).ok
    except requests.RequestException: return False
def generate(question,context,model=DEFAULT_MODEL,timeout=45):
    prompt=f"You are FundFlow, a finance and loan assistant. Answer only from the supplied context. Do not invent facts.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{question}\n\nANSWER:"
    r=requests.post(OLLAMA_URL,json={"model":model,"prompt":prompt,"stream":False,"options":{"temperature":0.1,"num_predict":220}},timeout=timeout)
    r.raise_for_status(); return (r.json().get("response") or "").strip()
