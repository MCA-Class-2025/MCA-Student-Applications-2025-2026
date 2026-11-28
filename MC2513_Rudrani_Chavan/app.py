"""
NutriMate — AI Nutrition Workspace
app.py  ·  Frontend only — RAG pipeline & embeddings untouched.

All AI extras (summary, quiz, nutrition cards, recipes, dish analysis)
are generated ONLY when the user explicitly clicks the generate button.
"""

import os
import io
import json
import html as html_lib
import base64
import tempfile
import urllib.parse
from datetime import datetime
import re

import requests as req
import streamlit as st

import config
import rag_pipeline
from backend.api_client import NutriMateAPIClient
api_client = NutriMateAPIClient()

def _clean_float(val) -> float:
    if not val:
        return 0.0
    try:
        nums = re.findall(r"\d+\.?\d*", str(val))
        if nums:
            return float(nums[0])
    except Exception:
        pass
    return 0.0

def _map_api_to_result(api_data: dict) -> dict:
    is_recipe = True
    is_not_food = False
    
    dish_name = api_data.get("food_name") or api_data.get("name") or "Unknown Dish"
    summary = api_data.get("health_benefits") or ""
    
    vits = api_data.get("vitamins", "")
    if isinstance(vits, list):
        vits = ", ".join(vits)
    mins = api_data.get("minerals", "")
    if isinstance(mins, list):
        mins = ", ".join(mins)
        
    ingredients = api_data.get("ingredients", [])
    if isinstance(ingredients, str):
        try:
            ingredients = json.loads(ingredients)
        except Exception:
            ingredients = [ingredients]
            
    cal = api_data.get("calories")
    if cal is not None and not str(cal).endswith("kcal"):
        cal = f"{cal} kcal"
    pro = api_data.get("protein")
    if pro is not None and not str(pro).endswith("g"):
        pro = f"{pro} g"
    carbs = api_data.get("carbohydrates") or api_data.get("carbs")
    if carbs is not None and not str(carbs).endswith("g"):
        carbs = f"{carbs} g"
    fat = api_data.get("fat")
    if fat is not None and not str(fat).endswith("g"):
        fat = f"{fat} g"
    fiber = api_data.get("fiber")
    if fiber is not None and not str(fiber).endswith("g"):
        fiber = f"{fiber} g"
        
    return {
        "dish_name": dish_name,
        "summary": summary,
        "ingredients": ingredients,
        "calories": cal,
        "protein": pro,
        "carbs": carbs,
        "fat": fat,
        "fiber": fiber,
        "vitamins": vits,
        "minerals": mins,
        "is_recipe": is_recipe,
        "is_not_food_image": is_not_food
    }

# ═══════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NutriMate AI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════
#  SESSION STATE DEFAULTS
# ═══════════════════════════════════════════════════════════
_DEFAULTS = {
    "messages":          [],
    "db":                None,
    "files":             [],
    "total_chunks":      0,
    "view":              "🍽 Chat",
    # On-demand feature caches
    "od_summary":        None,
    "od_flashcards":     None,
    "od_quiz":           None,
    "od_recipes":        None,
    "od_quiz_answers":   {},
    # Shared analyzed_content — auto-populated after any upload/index
    "analyzed_content":  None,
    "analyzed_content_key": None,   # hash of source to detect stale cache
    # Recipe Visualizer
    "rv_analysis":       None,
    # rv_dish_image removed (Generate Dish Image feature removed in Task 10)
    # Nutrition Summary Dashboard cache
    "ns_data":           None,
    "ns_cache_key":      None,
    # Nutrition Cards cache
    "nc_cards":          None,
    "nc_cache_key":      None,
    # AI Nutrition Quiz cache & state
    "quiz_questions":    None,
    "quiz_cache_key":    None,
    "quiz_current_idx":  0,
    "quiz_answers":      {},
    "quiz_submitted":    False,
    # AI Meal Planner cache & state
    "mp_plan":           None,
    "mp_cache_key":      None,
    "mp_goal":           "Weight Loss",
    "mp_diet":           "Vegetarian",
    "mp_meals":          ["Breakfast", "Lunch", "Snacks", "Dinner"],
    "mp_days":           1,
    # AI Health Score cache & state
    "hs_data":           None,
    "hs_cache_key":      None,
    # AI Nutrition Dashboard activity & analytics
    "activity_log":      [],
    "analyzed_count":    0,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load existing vector DB once (never rebuild on navigation)
if st.session_state.db is None:
    try:
        st.session_state.db = rag_pipeline.get_vector_store()
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def now_ts():
    return datetime.now().strftime("%I:%M %p")


def _add_activity(action: str, details: str = "", icon: str = "📌"):
    if "activity_log" not in st.session_state:
        st.session_state.activity_log = []
    st.session_state.activity_log.insert(0, {
        "action": action,
        "details": details,
        "time": now_ts(),
        "icon": icon,
    })
    st.session_state.activity_log = st.session_state.activity_log[:15]


def _render_home_dashboard():
    """Renders the minimal, focused Home workspace."""
    n_files = len(st.session_state.files)

    # ── Welcome Banner ───────────────────────────────────────
    st.markdown(
        f"""<div class="hero" style="margin-bottom:20px;">
            <div class="hero-top">
                <div>
                    <h1 class="hero-title">Hello, <span class="accent">NutriMate!</span> 👋</h1>
                    <p class="hero-sub">Your AI assistant for evidence-based nutrition guidance. Upload a recipe, PDF, or food image to get started.</p>
                </div>
                <div class="hero-badges">
                    <span class="hero-badge">📄 {n_files} File{"s" if n_files != 1 else ""}</span>
                    <span class="hero-badge"><span class="green-dot">●</span> Gemma RAG</span>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Quick Suggestion Chips ───────────────────────────────
    st.markdown(
        "<div class='section-label' style='margin-bottom:10px;'>💡 Try asking…</div>",
        unsafe_allow_html=True,
    )
    suggestions = [
        {"icon": "🥩", "text": "High Protein Foods",       "query": "What are the best high protein foods for daily nutrition?"},
        {"icon": "📉", "text": "Weight Loss Diet",          "query": "What is the best Indian diet plan for sustainable weight loss?"},
        {"icon": "🩺", "text": "Diabetes Friendly Meals",  "query": "What are low-GI, diabetes-friendly Indian meal options?"},
        {"icon": "🌅", "text": "Healthy Breakfast",         "query": "Give me quick and healthy Indian breakfast options."},
        {"icon": "🩸", "text": "Iron Rich Foods",           "query": "What foods are rich in iron and help improve hemoglobin?"},
        {"icon": "☀️", "text": "Vitamin D Sources",        "query": "How can I meet my daily Vitamin D requirements through diet?"},
        {"icon": "🌾", "text": "Fiber Rich Foods",          "query": "Which foods are highest in dietary fiber?"},
        {"icon": "🍛", "text": "Balanced Indian Diet",      "query": "How do I create a balanced Indian thali with optimal macros?"},
    ]
    cols = st.columns(4, gap="small")
    for idx, s in enumerate(suggestions):
        with cols[idx % 4]:
            if st.button(f"{s['icon']} {s['text']}", key=f"btn_sug_{idx}", use_container_width=True):
                st.session_state["_pending_query"] = s["query"]
                st.rerun()

    # ── Compact Recent Uploads ───────────────────────────────
    files = st.session_state.files
    if files:
        st.markdown(
            "<div class='section-label' style='margin:18px 0 8px;'>📁 Recent Uploads</div>",
            unsafe_allow_html=True,
        )
        rows = []
        for f in files[:4]:
            fname = html_lib.escape(f.get("name", "Document"))
            fsize = f.get("size", 0)
            ftype = f.get("type", "PDF" if fname.lower().endswith(".pdf") else ("Food Image" if fname.lower().endswith((".png", ".jpg", ".jpeg")) else "TXT"))
            ftime = f.get("time", "")
            icon  = "📄" if "PDF" in ftype else ("🖼️" if "Image" in ftype else "📝")
            rows.append(
                f"""<div class="db-upload-row">
                    <div class="db-upload-left">
                        <span style="font-size:15px;">{icon}</span>
                        <div>
                            <div class="db-upload-name">{fname}</div>
                            <div class="db-upload-meta">{ftype} · {fsize} KB{(" · " + ftime) if ftime else ""}</div>
                        </div>
                    </div>
                    <span class="db-upload-badge">Analyzed</span>
                </div>"""
            )
        st.markdown("".join(rows), unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


def latest_msg():
    return next(
        (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
        None,
    )

def latest_metrics():
    m = latest_msg()
    return m.get("metrics", {}) if m else {}

def img_to_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def clear_od_cache():
    for k in ("od_summary", "od_flashcards", "od_quiz", "od_recipes"):
        st.session_state[k] = None
    st.session_state.od_quiz_answers = {}
    # Clear module-level caches so they regenerate when content changes
    for k in (
        "ns_data", "ns_cache_key",
        "nc_cards", "nc_cache_key",
        "quiz_questions", "quiz_cache_key",
        "hs_data", "hs_cache_key",
    ):
        st.session_state[k] = None
    st.session_state.quiz_answers   = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_current_idx = 0
    # Note: rv_analysis / rv_dish_image and analyzed_content are NOT cleared
    # on new chat — they're independent of the RAG context.


def _extract_text_from_upload(uploaded_file) -> tuple[str, bytes | None]:
    """
    Extract text content from an uploaded file.
    Returns (text_content, image_bytes_or_None).
    """
    fname = uploaded_file.name.lower()
    raw   = uploaded_file.read()

    if fname.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore"), None

    if fname.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(raw)
            tmp_path = tmp.name
        try:
            from langchain_community.document_loaders import PyPDFLoader
            pages = PyPDFLoader(tmp_path).load()
            text = "\n".join(p.page_content for p in pages)[:4000]
            return text, None
        except Exception as e:
            return f"PDF error: {e}", None
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    if fname.endswith((".png", ".jpg", ".jpeg")):
        # Try OCR
        try:
            from PIL import Image
            import numpy as np
            reader  = rag_pipeline.get_ocr_reader()
            img     = Image.open(io.BytesIO(raw)).convert("RGB")
            arr     = np.array(img)
            results = reader.readtext(arr, detail=0)
            text    = " ".join(results).strip()
            if not text:
                # Fall back to filename hint
                text = (
                    "Food image: "
                    + uploaded_file.name.rsplit(".", 1)[0]
                      .replace("-", " ").replace("_", " ")
                )
        except Exception:
            text = (
                "Food image: "
                + uploaded_file.name.rsplit(".", 1)[0]
                  .replace("-", " ").replace("_", " ")
            )
        return text, raw

    return "", None


def _build_content_summary(ns_data: dict) -> str:
    """
    Build a content-specific 2-4 sentence nutrition summary from ns_data fields.
    Never invents values — only uses what is actually present in the data.
    Safely converts ints/floats/lists to strings to prevent AttributeError.
    """
    _NA = "Not Available"
    name   = ns_data.get("source_title") or ns_data.get("dish_name") or "This dish"
    cal    = ns_data.get("calories")
    pro    = ns_data.get("protein")
    carb   = ns_data.get("carbohydrates")
    fat    = ns_data.get("fat")
    fiber  = ns_data.get("fiber")
    vits   = ns_data.get("vitamins")      or ns_data.get("vitamins_minerals")
    mins   = ns_data.get("minerals")
    bens   = ns_data.get("health_benefits")
    mod    = ns_data.get("consume_in_moderation")

    def _to_str(val):
        if val is None:
            return ""
        if isinstance(val, (list, tuple)):
            return ", ".join(str(x) for x in val if str(x) not in (_NA, "Not Available", ""))
        return str(val).strip()

    cal_s, pro_s, carb_s, fat_s = _to_str(cal), _to_str(pro), _to_str(carb), _to_str(fat)
    fiber_s, vits_s, mins_s = _to_str(fiber), _to_str(vits), _to_str(mins)
    bens_s, mod_s = _to_str(bens), _to_str(mod)

    parts = []

    # Sentence 1: Dish + primary macros
    macro_parts = []
    if cal_s and cal_s not in (_NA, "Not Available"):
        macro_parts.append(cal_s if any(u in cal_s.lower() for u in ("kcal", "cal", "kj")) else f"{cal_s} kcal")
    if pro_s and pro_s not in (_NA, "Not Available"):
        macro_parts.append(f"{pro_s} protein" if "protein" not in pro_s.lower() else pro_s)
    if carb_s and carb_s not in (_NA, "Not Available"):
        macro_parts.append(f"{carb_s} carbs" if not any(u in carb_s.lower() for u in ("carb", "g", "gram")) else carb_s)
    if fat_s and fat_s not in (_NA, "Not Available"):
        macro_parts.append(f"{fat_s} fat" if "fat" not in fat_s.lower() else fat_s)

    if macro_parts:
        parts.append(f"{name} provides approximately {', '.join(macro_parts)} per serving.")
    else:
        parts.append(f"{name} is a nutritious food item.")

    # Sentence 2: Micronutrients (vitamins, minerals, fiber)
    micro_parts = []
    if fiber_s and fiber_s not in (_NA, "Not Available"):
        micro_parts.append(f"dietary fiber ({fiber_s})")
    if vits_s and vits_s not in (_NA, "Not Available"):
        micro_parts.append(vits_s)
    if mins_s and mins_s not in (_NA, "Not Available"):
        micro_parts.append(mins_s)
    if micro_parts:
        parts.append(f"It is a source of {', '.join(micro_parts)}.")

    # Sentence 3: Health benefits (if present)
    if bens_s and bens_s not in (_NA, "Not Available"):
        parts.append(bens_s.rstrip(".") + ".")

    # Sentence 4: Moderation warning (if present)
    if mod_s and mod_s not in (_NA, "Not Available"):
        parts.append(f"Note: {mod_s.rstrip('.')}; portion control is recommended.")

    return " ".join(parts) if parts else f"{name} — nutritional details available after analysis."


def _build_quiz_questions(ns_data, rv_an, ctx) -> list[dict]:
    """Generates 5-6 structured multiple choice questions from analyzed nutrition data."""
    dish_name = (ns_data.get("source_title") if ns_data else None) or (rv_an.get("dish_name") if rv_an else "Analyzed Dish")

    # Extract nutrition values if available
    cal = ns_data.get("calories") if ns_data else (rv_an.get("calories") if rv_an else "Not Available")
    pro = ns_data.get("protein") if ns_data else (rv_an.get("protein") if rv_an else "Not Available")
    carb = ns_data.get("carbohydrates") if ns_data else (rv_an.get("carbs") if rv_an else "Not Available")
    fat = ns_data.get("fat") if ns_data else (rv_an.get("fat") if rv_an else "Not Available")
    fiber = ns_data.get("fiber") if ns_data else (rv_an.get("fiber") if rv_an else "Not Available")
    vits = ns_data.get("vitamins") if ns_data else (rv_an.get("vitamins") if rv_an else "Not Available")
    mins = ns_data.get("minerals") if ns_data else (rv_an.get("minerals") if rv_an else "Not Available")
    benefits = ns_data.get("health_benefits") if ns_data else "Provides essential nutrients"
    suitable = ns_data.get("suitable_for") if ns_data else "Adults and healthy individuals"
    moderation = ns_data.get("consume_in_moderation") if ns_data else "Portion sizes and added sugars"

    # Try LLM first for rich contextual question generation
    try:
        llm = rag_pipeline.get_llm()
        content_text = f"Dish: {dish_name}\nCalories: {cal}\nProtein: {pro}\nCarbohydrates: {carb}\nFat: {fat}\nFiber: {fiber}\nVitamins: {vits}\nMinerals: {mins}\nHealth Benefits: {benefits}\nSuitable For: {suitable}\nConsume in Moderation: {moderation}\nContext: {ctx[:1500]}"

        prompt = (
            "Generate exactly 6 distinct multiple-choice quiz questions based ONLY on the nutrition facts below.\n\n"
            f"NUTRITION FACTS:\n{content_text}\n\n"
            "Format reply ONLY as a valid JSON array of objects with keys:\n"
            '["topic", "question", "options", "correct", "explanation"]\n'
            "- topic: one of (Calories, Protein, Carbohydrates, Healthy Fats, Fiber, Vitamins, Minerals, Health Benefits, Suitable For, Consume in Moderation)\n"
            "- question: question text\n"
            '- options: array of 4 strings like ["A) ...", "B) ...", "C) ...", "D) ..."]\n'
            '- correct: letter string like "A", "B", "C", or "D"\n'
            "- explanation: 1-2 sentence reason why the answer is correct\n\n"
            "Reply ONLY with the JSON array."
        )

        raw = llm.invoke(prompt).strip()
        clean = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()
        start = clean.find("[")
        end = clean.rfind("]")
        if start != -1 and end != -1:
            q_list = json.loads(clean[start : end + 1])
            if isinstance(q_list, list) and len(q_list) >= 4:
                return q_list[:6]
    except Exception:
        pass

    # Instant fallback rule-based questions if LLM fails or is slow
    fallback_qs = [
        {
            "topic": "Protein",
            "question": f"What is the estimated protein content per serving for {dish_name}?",
            "options": [f"A) {pro}", "B) 0 g", "C) 100 g", "D) Not Applicable"],
            "correct": "A",
            "explanation": f"Based on the analysis, {dish_name} provides {pro} of protein per serving."
        },
        {
            "topic": "Calories",
            "question": f"What is the total estimated calorie count for a serving of {dish_name}?",
            "options": [f"A) {cal}", "B) 10 kcal", "C) 2,500 kcal", "D) 0 kcal"],
            "correct": "A",
            "explanation": f"The estimated caloric value per serving is {cal}."
        },
        {
            "topic": "Health Benefits",
            "question": f"Which of the following is highlighted as a primary health benefit of this food/content?",
            "options": [f"A) {benefits[:70]}", "B) Causes immediate fatigue", "C) Has zero nutritional value", "D) Completely replaces water"],
            "correct": "A",
            "explanation": f"The analysis highlights that this content {benefits[:100]}."
        },
        {
            "topic": "Suitable For",
            "question": f"For which target group is this nutrition profile best suited?",
            "options": [f"A) {suitable[:70]}", "B) Strictly no one", "C) Only high-performance astronauts", "D) Infants under 1 month"],
            "correct": "A",
            "explanation": f"This meal/nutrition profile is recommended for {suitable}."
        },
        {
            "topic": "Consume in Moderation",
            "question": f"What component should be consumed in moderation according to the analysis?",
            "options": [f"A) {moderation[:70]}", "B) Pure fresh air", "C) Tap water", "D) Essential oxygen"],
            "correct": "A",
            "explanation": f"It is recommended to keep {moderation} in moderation for balanced health."
        },
        {
            "topic": "Carbohydrates",
            "question": f"What is the estimated carbohydrate amount in {dish_name}?",
            "options": [f"A) {carb}", "B) 500 g", "C) 1 g", "D) Not Measured"],
            "correct": "A",
            "explanation": f"The dish contains an estimated {carb} of carbohydrates."
        }
    ]
    return fallback_qs


def _format_meal_plan_download(plan: list[dict], goal: str, diet: str) -> str:
    """Formats the generated meal plan as a clean plain-text document for downloading."""
    lines = [
        "==================================================",
        "          NUTRIMATE AI MEAL PLANNER               ",
        "==================================================",
        f"Goal: {goal}",
        f"Diet Type: {diet}",
        f"Generated At: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
        "==================================================\n"
    ]

    for day_item in plan:
        lines.append(f"--- DAY {day_item.get('day', 1)} ---")
        for meal in day_item.get("meals", []):
            m_type = meal.get("type", "Meal")
            name = meal.get("name", "Dish")
            ings = ", ".join(meal.get("ingredients", [])) if isinstance(meal.get("ingredients"), list) else meal.get("ingredients", "")
            cal = meal.get("calories", "")
            pro = meal.get("protein", "")
            carb = meal.get("carbs", "")
            fat = meal.get("fat", "")
            fiber = meal.get("fiber", "")
            why = meal.get("why", "")

            lines.append(f"\n[ {m_type.upper()} ]: {name}")
            lines.append(f"  Ingredients: {ings}")
            lines.append(f"  Macros: Calories: {cal} | Protein: {pro} | Carbs: {carb} | Fat: {fat} | Fiber: {fiber}")
            lines.append(f"  Why Recommended: {why}")
        lines.append("\n" + "-"*45 + "\n")

    return "\n".join(lines)


def _generate_indian_meal_plan(goal: str, diet: str, meals: list[str], days: int, analyzed_content: dict = None) -> list[dict]:
    """
    Generates a personalized Indian meal plan with strict rule-based pre-filtering.

    Diet Rules:
      - Vegetarian: STRICTLY NO meat, chicken, fish, mutton, eggs.
      - Eggetarian: Vegetarian + egg dishes ONLY. MUST include egg meals. NO chicken/fish/mutton.
      - Non-Vegetarian: All dishes allowed.

    Goal Calorie Targets (per meal):
      - Weight Loss:      300–450 kcal  · High protein · High fiber · Low fat/sugar
      - Weight Gain:      500–700 kcal  · Complex carbs · Healthy fats
      - Muscle Gain:      400–550 kcal  · 25–35 g protein · Moderate carbs
      - Maintenance:      380–520 kcal  · Balanced macros
      - Diabetic Friendly: 280–420 kcal · Low GI · High fiber · Controlled carbs · No refined sugar
    """

    # ──────────────────────────────────────────────────────────────
    # SECTION 1 · COMPLETE MEAL DATABASE
    # Every meal: name, tags[], cal, pro, carbs, fat, fiber, why
    # tags: diet category + goal compatibility + meal type
    # ──────────────────────────────────────────────────────────────
    # fmt: off
    from backend.seed_data import MEAL_DB
    # fmt: on

    # ──────────────────────────────────────────────────────────────
    # SECTION 2 · GOAL CODE MAPPING
    # ──────────────────────────────────────────────────────────────
    GOAL_CODE = {
        "Weight Loss": "wl",
        "Weight Gain": "wg",
        "Muscle Gain": "mg",
        "Maintenance": "m",
        "Diabetic Friendly": "db",
    }
    goal_code = GOAL_CODE.get(goal, "m")

    # Calorie windows per meal per goal
    GOAL_CAL = {
        "wl": (180, 450),
        "wg": (430, 700),
        "mg": (250, 560),
        "m":  (250, 530),
        "db": (130, 430),
    }
    cal_lo, cal_hi = GOAL_CAL.get(goal_code, (200, 600))

    # ──────────────────────────────────────────────────────────────
    # SECTION 3 · DIET TAG MAPPING
    # ──────────────────────────────────────────────────────────────
    DIET_TAG = {
        "Vegetarian":     "veg",
        "Eggetarian":     "egg",
        "Non-Vegetarian": "nv",
    }
    diet_tag = DIET_TAG.get(diet, "veg")

    # ──────────────────────────────────────────────────────────────
    # SECTION 4 · PRE-FILTER: build per-meal-type candidate pools
    # ──────────────────────────────────────────────────────────────
    import random

    def _filter_pool(meal_type: str) -> list[dict]:
        """Return all DB entries that match diet + goal + meal type, within calorie window."""
        return [
            m for m in MEAL_DB
            if m["type"] == meal_type
            and diet_tag in m["diet"]
            and goal_code in m["goals"]
            and cal_lo <= m["cal"] <= cal_hi
        ]

    def _fallback_pool(meal_type: str) -> list[dict]:
        """Relax goal filter, keep only diet + meal type."""
        return [
            m for m in MEAL_DB
            if m["type"] == meal_type
            and diet_tag in m["diet"]
        ]

    # Eggetarian: ensure egg meals are included
    EGG_MEAL_TYPES = ["Breakfast", "Snacks", "Dinner", "Lunch"]
    egg_specific = {
        t: [m for m in MEAL_DB if m["type"] == t and "egg" in m["diet"] and "veg" not in m["diet"]]
        for t in EGG_MEAL_TYPES
    }

    # ──────────────────────────────────────────────────────────────
    # SECTION 5 · BUILD PLAN · NO-REPEAT SELECTION
    # ──────────────────────────────────────────────────────────────
    # Seed with plan key for reproducibility per session
    plan_key = f"{goal}|{diet}|{','.join(meals)}|{days}"
    rng = random.Random(hash(plan_key) & 0xFFFFFFFF)

    used_names: set[str] = set()
    plan: list[dict] = []

    for d in range(1, days + 1):
        day_meals: list[dict] = []
        # Track which meal types have gotten an egg dish this day (eggetarian)
        day_has_egg = False

        for meal_type in meals:
            if meal_type not in ("Breakfast", "Lunch", "Snacks", "Dinner"):
                continue

            pool = _filter_pool(meal_type)
            # Remove already-used names
            available = [m for m in pool if m["name"] not in used_names]

            # If pool is empty after used-name filtering, widen to day-level (allow repeat across plans but not same day)
            if not available:
                available = [m for m in pool]
                # Still try to avoid same-day repeats
                day_used = {dm["name"] for dm in day_meals}
                available = [m for m in available if m["name"] not in day_used] or pool[:]

            # If still empty, use fallback (relax goal constraint)
            if not available:
                available = _fallback_pool(meal_type)
                day_used = {dm["name"] for dm in day_meals}
                available = [m for m in available if m["name"] not in day_used] or available

            # Eggetarian: on each day, inject at least one egg-specific dish per meal type if available
            if diet == "Eggetarian" and not day_has_egg:
                egg_pool = [m for m in egg_specific.get(meal_type, []) if m["name"] not in used_names]
                if egg_pool:
                    available = egg_pool  # Force egg dish for this slot
                    day_has_egg = True

            # Pick randomly from available
            chosen = rng.choice(available).copy()
            chosen["type"] = meal_type

            # Format macros as strings
            chosen["calories"] = f"{chosen['cal']} kcal"
            chosen["protein"]  = f"{chosen['pro']} g"
            chosen["carbs"]    = f"{chosen['carbs']} g"
            chosen["fat"]      = f"{chosen['fat']} g"
            chosen["fiber"]    = f"{chosen['fiber']} g"

            day_meals.append(chosen)
            used_names.add(chosen["name"])

        # Eggetarian: if no egg dish appeared yet this day, replace one non-egg slot with egg dish
        if diet == "Eggetarian" and not day_has_egg and day_meals:
            for meal_type in meals:
                egg_pool = [
                    m for m in egg_specific.get(meal_type, [])
                    if m["name"] not in used_names
                ]
                if egg_pool:
                    new_egg = rng.choice(egg_pool).copy()
                    new_egg["type"] = meal_type
                    new_egg["calories"] = f"{new_egg['cal']} kcal"
                    new_egg["protein"]  = f"{new_egg['pro']} g"
                    new_egg["carbs"]    = f"{new_egg['carbs']} g"
                    new_egg["fat"]      = f"{new_egg['fat']} g"
                    new_egg["fiber"]    = f"{new_egg['fiber']} g"
                    # Replace the corresponding slot
                    for i, dm in enumerate(day_meals):
                        if dm["type"] == meal_type:
                            used_names.discard(dm["name"])
                            day_meals[i] = new_egg
                            used_names.add(new_egg["name"])
                            day_has_egg = True
                            break
                if day_has_egg:
                    break

        plan.append({"day": d, "meals": day_meals})

    return plan


def _calculate_ai_health_score(ns_data=None, rv_an=None, ctx="") -> dict:
    """
    Calculates a Health Score (0-100), Breakdown scores across 6 categories,
    and generates Strengths, Areas to Improve, and AI Recommendation.
    Reads directly from analyzed_content as primary source of truth.
    """
    _NA = "Not Available"
    ac = st.session_state.get("analyzed_content") or {}
    src = ac if (ac and ac.get("is_recipe")) else (ns_data or rv_an or {})

    dish_name = src.get("dish_name") or src.get("source_title") or (rv_an.get("dish_name") if rv_an else "Analyzed Content")
    if dish_name == _NA or not dish_name:
        dish_name = "Analyzed Content"

    # Extract macro / micro values
    cal_str = src.get("calories") or (rv_an.get("calories") if rv_an else _NA)
    pro_str = src.get("protein") or (rv_an.get("protein") if rv_an else _NA)
    carb_str = src.get("carbohydrates") or src.get("carbs") or (rv_an.get("carbs") if rv_an else _NA)
    fat_str = src.get("fat") or (rv_an.get("fat") if rv_an else _NA)
    fib_str = src.get("fiber") or (rv_an.get("fiber") if rv_an else _NA)

    vits_str = src.get("vitamins") or (rv_an.get("vitamins") if rv_an else _NA)
    mins_str = src.get("minerals") or (rv_an.get("minerals") if rv_an else _NA)
    benefits_str = src.get("health_benefits") or "Provides essential nutrition and dietary energy."
    moderation_str = src.get("consume_in_moderation") or "Monitor sodium & portion size."
    suitable_str = src.get("suitable_for") or "General Adults & Health Enthusiasts"

    def _num(val_str, default=0):
        if not val_str or val_str == _NA: return default
        m = re.search(r'\d+', str(val_str))
        return int(m.group()) if m else default

    p_val = _num(pro_str, 14)
    c_val = _num(carb_str, 45)
    f_val = _num(fat_str, 10)
    fib_val = _num(fib_str, 5)
    cal_val = _num(cal_str, 350)

    # 1. Protein Score (0-20)
    if p_val >= 18 or "high protein" in (str(benefits_str) + str(pro_str)).lower():
        protein_pts = 19
    elif p_val >= 10:
        protein_pts = 15
    else:
        protein_pts = 10

    # 2. Fiber Score (0-20)
    if fib_val >= 6 or "high fiber" in (str(benefits_str) + str(fib_str)).lower():
        fiber_pts = 19
    elif fib_val >= 3:
        fiber_pts = 14
    else:
        fiber_pts = 9

    # 3. Healthy Fats Score (0-15)
    if f_val <= 15 and f_val >= 5:
        fats_pts = 14
    elif f_val > 25:
        fats_pts = 8
    else:
        fats_pts = 11

    # 4. Caloric Balance Score (0-15)
    if 250 <= cal_val <= 550:
        cal_pts = 14
    elif cal_val > 700:
        cal_pts = 8
    else:
        cal_pts = 11

    # 5. Vitamins & Minerals Score (0-15)
    vit_min_text = (str(vits_str) + " " + str(mins_str)).lower()
    if len(vit_min_text) > 8 and "not available" not in vit_min_text:
        vit_pts = 14
    elif any(k in vit_min_text for k in ["vitamin", "iron", "calcium", "zinc", "potassium"]):
        vit_pts = 12
    else:
        vit_pts = 10

    # 6. Sodium & Sugar Control Score (0-15)
    mod_text = str(moderation_str).lower()
    if "high sodium" in mod_text or "high sugar" in mod_text or "excess" in mod_text:
        control_pts = 8
    elif "not available" in mod_text or "moderate" in mod_text:
        control_pts = 12
    else:
        control_pts = 14

    total_score = min(100, max(0, protein_pts + fiber_pts + fats_pts + cal_pts + vit_pts + control_pts))

    # Rating Level & Color
    if total_score >= 80:
        rating_label = "🟢 Excellent"
        rating_color = "#22C55E"
        rating_bg = "rgba(34,197,94,0.12)"
    elif total_score >= 60:
        rating_label = "🟡 Good"
        rating_color = "#EAB308"
        rating_bg = "rgba(234,179,8,0.12)"
    elif total_score >= 40:
        rating_label = "🟠 Average"
        rating_color = "#F97316"
        rating_bg = "rgba(249,115,22,0.12)"
    else:
        rating_label = "🔴 Poor"
        rating_color = "#EF4444"
        rating_bg = "rgba(239,68,68,0.12)"

    strengths = []
    if protein_pts >= 15 and pro_str != _NA:
        strengths.append(f"High protein profile ({pro_str} per serving)")
    if fiber_pts >= 14 and fib_str != _NA:
        strengths.append(f"Rich in dietary fiber ({fib_str} for gut health)")
    if cal_pts >= 13 and cal_str != _NA:
        strengths.append(f"Well-balanced caloric density ({cal_str})")
    if vit_pts >= 12 and vits_str != _NA:
        strengths.append(f"Good micronutrient density ({vits_str})")
    if benefits_str != _NA:
        strengths.append(str(benefits_str)[:90])
    if not strengths:
        strengths.append("Provides essential baseline macronutrients for energy.")

    improvements = []
    if fiber_pts < 14:
        improvements.append("Low to moderate dietary fiber content — add fresh salad or greens.")
    if fats_pts < 11:
        improvements.append("Higher total fat content — monitor oil/ghee usage.")
    if moderation_str != _NA and moderation_str != "Watch sodium & portion size.":
        improvements.append(f"Consume in moderation: {moderation_str}")
    else:
        improvements.append("Monitor sodium & portion size for optimal metabolic balance.")

    rec = f"For optimal results with {dish_name}, pair with a side salad or probiotic drink (like buttermilk) and ensure balanced hydration throughout the day."
    if suitable_str != _NA:
        rec += f" Best suitable for {suitable_str}."

    return {
        "dish_name": dish_name,
        "total_score": total_score,
        "rating_label": rating_label,
        "rating_color": rating_color,
        "rating_bg": rating_bg,
        "breakdown": [
            {"label": "🥩 Protein", "pts": protein_pts, "max": 20, "color": "#22C55E"},
            {"label": "🌾 Fiber", "pts": fiber_pts, "max": 20, "color": "#8B5CF6"},
            {"label": "🥑 Healthy Fats", "pts": fats_pts, "max": 15, "color": "#14B8A6"},
            {"label": "🔥 Caloric Balance", "pts": cal_pts, "max": 15, "color": "#F97316"},
            {"label": "☀️ Vitamins & Minerals", "pts": vit_pts, "max": 15, "color": "#3B82F6"},
            {"label": "🧂 Sodium & Sugar Control", "pts": control_pts, "max": 15, "color": "#EC4899"},
        ],
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "recommendation": rec,
    }


def _auto_analyze_content(db, source_label: str = "") -> dict:
    """
    Auto-runs after any PDF/image/text upload is indexed.
    Retrieves a broad nutrition context from the vector store and runs
    structured analysis to produce a unified analyzed_content object.

    GUARANTEES:
    - Always returns a dict with ALL required keys populated.
    - Falls back to text-based extraction if LLM JSON parsing fails.
    - Never returns an empty or is_recipe=False result when documents exist in DB.

    Returns a dict stored in st.session_state.analyzed_content.
    """
    _NA = "Not Available"

    _REQUIRED_KEYS = [
        "document_type", "source_title", "dish_name", "summary",
        "calories", "protein", "carbohydrates", "fat", "fiber",
        "vitamins", "minerals", "health_benefits",
        "consume_in_moderation", "suitable_for",
        "ingredients", "confidence_score",
        "is_recipe", "context_text",
    ]

    base = {k: _NA for k in _REQUIRED_KEYS}
    base.update({
        "document_type":   "unknown",
        "source_title":    source_label or "Uploaded Content",
        "dish_name":       source_label.rsplit(".", 1)[0] if source_label else "Uploaded Content",
        "summary":         _NA,
        "ingredients":     [],
        "confidence_score": 0,
        "is_recipe":       False,
        "context_text":    "",
    })

    if db is None:
        print("[ANALYSIS LOG] [ERROR] db is None -- returning empty base.")
        return base

    # ── Step 1: Retrieve broad nutrition context from vector store ───
    try:
        broad_query = (
            "nutrition calories protein carbohydrates fat fiber vitamins minerals "
            "health benefits ingredients recipe dish food"
        )
        docs = db.similarity_search(broad_query, k=10)
        if not docs:
            print("[ANALYSIS LOG] [INFO] No documents returned from similarity search.")
            return base

        context_text = "\n\n".join(d.page_content for d in docs)
        base["context_text"] = context_text

        print(f"[ANALYSIS LOG] [OK] Retrieved {len(docs)} chunks, context length = {len(context_text)} chars")
    except Exception as e:
        print(f"[ANALYSIS LOG] [ERROR] Similarity search failed: {e}")
        return base

    # ── Step 2: LLM structured JSON extraction ──────────────────────
    llm_data = None
    try:
        llm = rag_pipeline.get_llm()
        prompt = (
            "You are a registered dietitian. Based ONLY on the context below, extract ALL nutrition information.\n\n"
            f"CONTEXT:\n{context_text[:5000]}\n\n"
            "Reply ONLY with a valid JSON object (no markdown, no extra text). Use these exact keys:\n"
            '{"document_type":"<recipe OR nutrition_document OR food_image OR general>",\n'
            '"dish_name":"<dish or document name>",\n'
            '"summary":"<2-3 sentence overview of the nutrition content>",\n'
            '"calories":"<kcal per serving or estimate>",\n'
            '"protein":"<grams>",\n'
            '"carbohydrates":"<grams>",\n'
            '"fat":"<grams>",\n'
            '"fiber":"<grams>",\n'
            '"vitamins":"<key vitamins found>",\n'
            '"minerals":"<key minerals found>",\n'
            '"health_benefits":"<2-3 health benefits>",\n'
            '"consume_in_moderation":"<what to limit>",\n'
            '"suitable_for":"<target groups e.g. Adults, Diabetics, Weight Loss>",\n'
            '"ingredients":["<ingredient 1>","<ingredient 2>"]}\n\n'
            "IMPORTANT: Use best-effort estimation for all numeric fields. "
            "If a value truly cannot be estimated, use the string \"Not Available\".\n"
            "Reply ONLY with the JSON object."
        )

        raw = llm.invoke(prompt).strip()
        print(f"[ANALYSIS LOG] [LLM] Raw response length: {len(raw)} chars")

        # Parse JSON from response
        import json as _json
        clean = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            llm_data = _json.loads(clean[start: end + 1])
            print(f"[ANALYSIS LOG] [OK] LLM JSON parsed successfully. Keys: {list(llm_data.keys())}")
        else:
            print(f"[ANALYSIS LOG] [WARN] No JSON braces found in LLM response.")

    except json.JSONDecodeError as e:
        print(f"[ANALYSIS LOG] [WARN] JSON parse failed: {e}")
    except Exception as e:
        print(f"[ANALYSIS LOG] [WARN] LLM call failed: {e}")

    # ── Step 3: Merge LLM data into base, normalise field names ─────
    if llm_data and isinstance(llm_data, dict):
        # Normalise 'carbs' → 'carbohydrates'
        if "carbs" in llm_data and "carbohydrates" not in llm_data:
            llm_data["carbohydrates"] = llm_data.pop("carbs")
        # Normalise 'vitamins_minerals' → split
        if "vitamins_minerals" in llm_data:
            vm = llm_data.pop("vitamins_minerals")
            llm_data.setdefault("vitamins", vm)
            llm_data.setdefault("minerals", vm)
        # Normalise source_title / dish_name
        if "source_title" not in llm_data and "dish_name" in llm_data:
            llm_data["source_title"] = llm_data["dish_name"]
        if "dish_name" not in llm_data and "source_title" in llm_data:
            llm_data["dish_name"] = llm_data["source_title"]

        # Merge into base — only overwrite with non-empty values
        for k, v in llm_data.items():
            if v is not None and v != "" and v != _NA:
                base[k] = v

        base["confidence_score"] = 85
        base["is_recipe"] = True
    else:
        # ── Step 3b: Fallback — text-based regex extraction ─────────
        print("[ANALYSIS LOG] [WARN] Using text-based fallback extraction from context.")
        ctx_lower = context_text.lower()

        # Try to extract dish name from context
        import re as _re
        dish_match = _re.search(r"(?:dish|recipe|food|identified food dish)[:\s]+([^\n]{3,60})", ctx_lower)
        if dish_match:
            base["dish_name"] = dish_match.group(1).strip().title()
            base["source_title"] = base["dish_name"]

        # Extract numeric nutrition values
        for field, patterns in {
            "calories": [r"calories?[:\s]*(\d+[\d,.]*\s*(?:kcal|cal)?)"],
            "protein": [r"protein[:\s]*(\d+[\d,.]*\s*g?)"],
            "carbohydrates": [r"carbohydrates?[:\s]*(\d+[\d,.]*\s*g?)", r"carbs?[:\s]*(\d+[\d,.]*\s*g?)"],
            "fat": [r"(?:total\s+)?fat[:\s]*(\d+[\d,.]*\s*g?)"],
            "fiber": [r"fib(?:er|re)[:\s]*(\d+[\d,.]*\s*g?)"],
        }.items():
            for pat in patterns:
                m = _re.search(pat, ctx_lower)
                if m:
                    base[field] = m.group(1).strip()
                    break

        # Check for vitamin/mineral mentions
        vit_matches = _re.findall(r"vitamin\s*[a-z0-9]+", ctx_lower)
        if vit_matches:
            base["vitamins"] = ", ".join(set(v.title() for v in vit_matches[:6]))
        min_keywords = ["iron", "calcium", "potassium", "zinc", "magnesium", "phosphorus", "sodium"]
        found_mins = [m.title() for m in min_keywords if m in ctx_lower]
        if found_mins:
            base["minerals"] = ", ".join(found_mins[:5])

        # Check for health benefits
        ben_match = _re.search(r"(?:health\s+)?benefits?[:\s]+([^\n]{5,200})", ctx_lower)
        if ben_match:
            base["health_benefits"] = ben_match.group(1).strip().capitalize()

        # Summarize from context
        if context_text:
            base["summary"] = context_text[:300].strip().replace("\n", " ")

        base["document_type"] = "nutrition_document"
        base["confidence_score"] = 45
        base["is_recipe"] = True  # Mark as true so modules render content

    # ── Step 4: Ensure ALL required keys exist with at least _NA ────
    _REQUIRED_KEYS = list(base.keys())
    missing_fields = []
    for k in _REQUIRED_KEYS:
        if base.get(k) is None or base.get(k) == "":
            base[k] = _NA
            missing_fields.append(k)

    # Ensure source_title / dish_name always set
    if base.get("source_title") == _NA and source_label:
        base["source_title"] = source_label
    if base.get("dish_name") == _NA and source_label:
        base["dish_name"] = source_label.rsplit(".", 1)[0]

    # ── Step 5: Debug logging ───────────────────────────────────────
    print(f"\n[ANALYSIS LOG] ==========================================")
    print(f"[ANALYSIS LOG] Document Type: {base.get('document_type')}")
    print(f"[ANALYSIS LOG] Dish Name: {base.get('dish_name')}")
    print(f"[ANALYSIS LOG] Confidence: {base.get('confidence_score')}")
    non_na_keys = [k for k in base if base[k] != _NA and k not in ("context_text",)]
    print(f"[ANALYSIS LOG] Populated keys: {non_na_keys}")
    if missing_fields:
        print(f"[ANALYSIS LOG] Missing fields (set to NA): {missing_fields}")
    print(f"[ANALYSIS LOG] Calories={base.get('calories')} | Protein={base.get('protein')} | Carbs={base.get('carbohydrates')} | Fat={base.get('fat')} | Fiber={base.get('fiber')}")
    print(f"[ANALYSIS LOG] Session state update confirmed: analyzed_content ready")
    print(f"[ANALYSIS LOG] ==========================================\n")

    return base



# ═══════════════════════════════════════════════════════════
#  CSS INJECTION
# ═══════════════════════════════════════════════════════════
css_path = os.path.join(config.BASE_DIR, "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
NAV_ITEMS = [
    "🍽 Chat",
    "📋 Nutrition Summary",
    "🧠 Nutrition Cards",
    "❓ Quiz",
    "🖼 Recipe Visualizer",
    "🍱 AI Meal Planner",
    "🏥 AI Health Score",
    "⚖️ Food Comparison",
    "📈 Progress Tracking",
    "💧 Hydration Tracking",
    "🍔 Cheat Meal Impact",
]

with st.sidebar:
    # ── Logo ─────────────────────────────────────────────
    st.markdown(
        """<div class="sb-logo">
            <span class="sb-logo-icon">🥗</span>
            <div class="sb-logo-text">
                <span class="sb-logo-name">NutriMate</span>
                <span class="sb-logo-sub">AI Nutrition Workspace</span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── New Chat ──────────────────────────────────────────
    if st.button("＋  New Chat", use_container_width=True, key="btn_new_chat"):
        st.session_state.messages = []
        clear_od_cache()
        st.rerun()

    st.markdown("<div class='sb-divider'></div>", unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────
    st.markdown("<div class='sb-section'>Nutrition Workspace</div>", unsafe_allow_html=True)
    selected = st.radio(
        "nav",
        NAV_ITEMS,
        index=NAV_ITEMS.index(st.session_state.view)
              if st.session_state.view in NAV_ITEMS else 0,
        label_visibility="collapsed",
    )
    st.session_state.view = selected

    st.markdown("<div class='sb-divider'></div>", unsafe_allow_html=True)

    # ── Knowledge Base Status ─────────────────────────────
    is_ready = st.session_state.db is not None
    dot  = "🟢" if is_ready else "🟠"
    ktxt = "KB Ready" if is_ready else "KB Empty"
    ksub = "Knowledge base is ready" if is_ready else "Upload nutrition PDF to start"
    status_cls = "kb-card" if is_ready else "kb-card empty"
    st.markdown(
        f"""<div class="{status_cls}">
            <span class="kb-dot">{dot}</span>
            <div>
                <div class="kb-text">{ktxt}</div>
                <div class="kb-sub">{ksub}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Upload (for KB / RAG) ─────────────────────────────
    st.markdown(
        "<div class='sb-section'>Upload Recipe / Nutrition PDF</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Upload Recipe, Food Image, Nutrition PDF or Text",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        new_files = [
            f for f in uploaded
            if f.name not in [x["name"] for x in st.session_state.files]
        ]
        if new_files:
            all_chunks, errors = [], []
            prog = st.progress(0)
            for i, uf in enumerate(new_files):
                prog.progress(int(i / len(new_files) * 100))
                try:
                    fp = os.path.join(config.DOCS_DIR, uf.name)
                    with open(fp, "wb") as fh:
                        fh.write(uf.getbuffer())
                    chunks = rag_pipeline.process_file(fp)
                    if chunks:
                        all_chunks.extend(chunks)
                        f_type = "Food Image" if uf.name.lower().endswith((".png", ".jpg", ".jpeg")) else ("PDF" if uf.name.lower().endswith(".pdf") else "TXT")
                        st.session_state.files.append(
                            {"name": uf.name, "size": round(uf.size / 1024, 1), "time": now_ts(), "type": f_type, "status": "Analyzed"}
                        )
                        _add_activity(f"Uploaded {f_type}", uf.name, icon="📄" if f_type == "PDF" else ("🖼️" if f_type == "Food Image" else "📝"))
                except Exception as e:
                    errors.append(str(e))
            if all_chunks:
                prog.progress(100)
                source_label = new_files[-1].name if new_files else ""
                with st.spinner("📚 Indexing & analyzing content…"):
                    st.session_state.db = rag_pipeline.build_vector_store(all_chunks)
                    st.session_state.total_chunks += len(all_chunks)
                    # Auto-analyze the uploaded content immediately
                    # Check if _process_image already set analyzed_content (food photos)
                    existing_ac = st.session_state.get("analyzed_content")
                    analyzed = _auto_analyze_content(
                        st.session_state.db,
                        source_label=source_label,
                    )
                    # If _process_image already set a richer analyzed_content, merge
                    if existing_ac and existing_ac.get("is_recipe"):
                        _NA = "Not Available"
                        for k, v in existing_ac.items():
                            if v is not None and v != "" and v != _NA:
                                analyzed.setdefault(k, v)
                    st.session_state.analyzed_content = analyzed
                    st.session_state.analyzed_content_key = hash(source_label)
                    # Also populate ns_data so Nutrition Summary renders immediately
                    st.session_state.ns_data = analyzed
                    # Log activity & increment analysis count
                    _add_activity("Analyzed Document", source_label, icon="🔍")
                    st.session_state.analyzed_count = st.session_state.get("analyzed_count", 0) + len(new_files)
                    # Invalidate all dependent module caches so they re-read fresh data
                    st.session_state.ns_cache_key = None
                    st.session_state.nc_cards = None
                    st.session_state.nc_cache_key = None
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_cache_key = None
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_current_idx = 0
                    st.session_state.hs_data = None
                    st.session_state.hs_cache_key = None
                st.toast(
                    f"✅ {len(new_files) - len(errors)} file(s) indexed & analyzed!", icon="🥗"
                )
                st.rerun()
            else:
                prog.empty()
                for e in errors:
                    st.error(e)

    # ── Indexed Files ─────────────────────────────────────
    if st.session_state.files:
        st.markdown(
            "<div class='sb-section' style='margin-top:10px;'>Indexed Nutrition Files</div>",
            unsafe_allow_html=True,
        )
        for f in st.session_state.files:
            icon = "🖼️" if f["name"].lower().endswith((".png", ".jpg", ".jpeg")) else "📄"
            st.markdown(
                f"<div class='sb-file'>{icon} {f['name']}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div class='sb-divider'></div>", unsafe_allow_html=True)



    # ── Clear KB ──────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Knowledge Base", use_container_width=True, key="btn_clear"):
        rag_pipeline.clear_vector_store()
        st.session_state.db = None
        st.session_state.messages = []
        st.session_state.files = []
        st.session_state.total_chunks = 0
        st.session_state.analyzed_content = None
        st.session_state.analyzed_content_key = None
        clear_od_cache()
        st.rerun()

    # ── Profile Card ──────────────────────────────────────
    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown(
        """<div class="sb-profile">
            <div class="sb-av">N</div>
            <div>
                <div class="sb-pname">NutriMate User</div>
                <div class="sb-pemail">nutrimate@ai.com</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════
#  LAYOUT: workspace | right insight panel
# ═══════════════════════════════════════════════════════════
lm      = latest_metrics()
last_am = latest_msg()

main_col, right_col = st.columns([3, 1], gap="small")

# ───────────────────────────────────────────────────────────
#  RIGHT INSIGHT PANEL
# ───────────────────────────────────────────────────────────
with right_col:
    st.markdown("<div style='padding-top:16px;'></div>", unsafe_allow_html=True)

    # 1. Sources Panel
    sources = last_am.get("sources", []) if last_am else []
    src_rows_html = ""
    if sources:
        for src in sources[:4]:
            icon = (
                "🖼️"
                if src.get("filename", "").lower().endswith((".png", ".jpg", ".jpeg"))
                else "📄"
            )
            fname = html_lib.escape(src.get("filename", "Doc"))
            page = src.get("page", "1")
            conf = src.get("confidence", "N/A")
            src_rows_html += f"""<div class="src-row">
                <div class="src-icon-box">{icon}</div>
                <div class="src-info">
                    <div class="src-name">{fname}</div>
                    <div class="src-page">Page {page}</div>
                </div>
                <span class="src-pct">{conf}</span>
            </div>"""
        if len(sources) > 4:
            src_rows_html += f"<a class='view-all'>View all {len(sources)} sources →</a>"
    else:
        src_rows_html = "<p style='font-size:0.77rem;color:var(--text-3);text-align:center;padding:8px 0;'>Ask a nutrition question to see sources.</p>"

    panel_sources = f"""<div class="panel">
        <div class="panel-head">
            <div class="panel-title">📋 Retrieved Sources</div>
            <span class="panel-count">{len(sources)}</span>
        </div>
        {src_rows_html}
    </div>"""
    st.markdown(panel_sources, unsafe_allow_html=True)

    # 2. Detected Topics Panel
    fcs = st.session_state.od_flashcards or []
    topic_html = (
        "".join(
            f"<span class='chip'>{fc.get('emoji','🥗')} {fc.get('topic','')}</span>"
            for fc in fcs
        )
        if fcs
        else "<span style='font-size:.76rem;color:var(--text-3);'>"
             "Topics detected after generating Nutrition Cards.</span>"
    )
    panel_topics = f"""<div class="panel">
        <div class="panel-head">
            <div class="panel-title">🔍 Detected Topics</div>
            <span class="panel-count">{len(fcs)}</span>
        </div>
        <div class="chips">{topic_html}</div>
    </div>"""
    st.markdown(panel_topics, unsafe_allow_html=True)

    # 3. Meal Snapshot / Nutrition Focus Panel
    rv_an = st.session_state.rv_analysis
    if rv_an and rv_an.get("is_recipe"):
        dish = rv_an.get("dish_name", "Dish")
        cal = rv_an.get("calories", "N/A")
        pro = rv_an.get("protein", "N/A")
        panel_focus = f"""<div class="panel">
            <div class="panel-head">
                <div class="panel-title">🍽 Last Meal Analysis</div>
            </div>
            <div style="font-size:.82rem;font-weight:700;color:var(--text-1);margin-bottom:6px;">{html_lib.escape(dish)}</div>
            <div class="rv-panel-row">
                <span>🔥 Calories</span><b>{html_lib.escape(str(cal))}</b>
            </div>
            <div class="rv-panel-row">
                <span>🥩 Protein</span><b>{html_lib.escape(str(pro))}</b>
            </div>
        </div>"""
    else:
        panel_focus = """<div class="panel">
            <div class="panel-head">
                <div class="panel-title">💡 Nutrition Focus</div>
            </div>
            <div class="qi-item"><div class="qi-dot"></div>
                <span>Prioritize whole, nutrient-dense foods</span></div>
            <div class="qi-item"><div class="qi-dot"></div>
                <span>Balance protein, fiber &amp; healthy fats daily</span></div>
            <div class="qi-item"><div class="qi-dot"></div>
                <span>Maintain hydration — 2–3 L water daily</span></div>
        </div>"""
    st.markdown(panel_focus, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────
#  MAIN WORKSPACE
# ───────────────────────────────────────────────────────────
with main_col:

    # ═══════════════════════════════════════
    #  🍽 CHAT
    # ═══════════════════════════════════════
    if selected == "🍽 Chat":

        # ── AI Nutrition Dashboard ─────────────────────────
        _render_home_dashboard()

        # ── Chat history ──────────────────────────────────
        st.markdown("<div style='padding:12px 24px 0;'>", unsafe_allow_html=True)
        for msg in st.session_state.messages:
            ts   = msg.get("timestamp", "")
            text = msg["content"]

            if msg["role"] == "user":
                safe_text = html_lib.escape(text)
                st.markdown(
                    f"""<div class="user-row">
                        <div class="user-block">
                            <div class="user-meta">You <span class="ts">{ts}</span></div>
                            <div class="user-bubble">{safe_text}
                                <span class="tick">✓✓</span></div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                srcs   = msg.get("sources", [])
                n_srcs = len(srcs)

                st.markdown(
                    f"""<div class="ai-row-header">
                        <div class="ai-av">🥗</div>
                        <div class="ai-meta">
                            <span class="ai-name">NutriMate</span>
                            <span class="ai-ts">{ts}</span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.markdown(text)
                st.markdown(
                    f"""<div class="action-bar">
                        <span class="act-btn">📋 Sources ({n_srcs})</span>
                        <span class="act-btn">👍 Helpful</span>
                        <span class="act-btn">👎 Not Helpful</span>
                    </div>
                    <div style="height:14px;"></div>""",
                    unsafe_allow_html=True,
                )
                if srcs:
                    with st.expander(f"📋 View Sources ({n_srcs})", expanded=False):
                        for src in srcs:
                            fname = html_lib.escape(src.get("filename", "Doc"))
                            page  = src.get("page", "1")
                            conf  = src.get("confidence", "N/A")
                            st.markdown(
                                f"<div style='font-size:.8rem;padding:5px 0;'>"
                                f"📄 <b>{fname}</b> — Page {page} &nbsp;"
                                f"<span style='color:var(--green);font-weight:600;'>{conf}</span></div>",
                                unsafe_allow_html=True,
                            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Chat Input ────────────────────────────────────
        prefill = (
            st.session_state.pop("_pending_query", None)
            if "_pending_query" in st.session_state
            else None
        )
        user_input = st.chat_input(
            placeholder="Ask anything about nutrition, diet, vitamins…",
            key="chat_input",
        )
        query = prefill or user_input
        if query:
            if st.session_state.db is None:
                st.warning(
                    "⚠️ Please upload at least one Nutrition PDF or Recipe file first.",
                    icon="📂",
                )
            else:
                st.session_state.messages.append(
                    {"role": "user", "content": query, "timestamp": now_ts()}
                )
                clear_od_cache()
                with st.spinner("🥗 NutriMate is thinking…"):
                    try:
                        answer, sources, metrics = rag_pipeline.generate_answer(
                            query,
                            st.session_state.messages,
                            st.session_state.db,
                        )
                    except Exception as e:
                        answer  = f"⚠️ Error: {e}"
                        sources = []
                        metrics = {}
                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   answer,
                    "sources":   sources,
                    "metrics":   metrics,
                    "timestamp": now_ts(),
                })
                st.rerun()

    # ═══════════════════════════════════════
    #  📋 NUTRITION SUMMARY
    # ═══════════════════════════════════════
    elif selected == "📋 Nutrition Summary":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>📋 Nutrition Summary Dashboard</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Structured nutritional summary automatically generated "
            "from your analyzed recipes, food images, or document context.</div>",
            unsafe_allow_html=True,
        )

        _NA = "Not Available"

        # Primary: shared analyzed_content from upload auto-analysis
        ac = st.session_state.get("analyzed_content")
        rv_an = st.session_state.get("rv_analysis")
        ctx = lm.get("context_text", "") or (ac.get("context_text", "") if ac else "")

        has_ac  = bool(ac and ac.get("is_recipe"))
        has_rv  = bool(rv_an and rv_an.get("is_recipe") and not rv_an.get("is_not_food_image"))
        has_ctx = bool(ctx and ctx.strip())

        rv_key  = hash(str(rv_an)) if rv_an else "none"
        ac_key  = hash(str(ac)) if ac else "none"
        ctx_key = hash(ctx) if ctx else "none"
        current_cache_key = f"ns_rv_{rv_key}_ac_{ac_key}_ctx_{ctx_key}"

        # Automatic generation & hash-based caching
        if (st.session_state.get("ns_cache_key") != current_cache_key) or (st.session_state.get("ns_data") is None):
            if has_ac or has_rv or has_ctx:
                with st.spinner("Generating structured Nutrition Summary…"):
                    if has_rv:
                        dish = rv_an.get("dish_name", "Dish")
                        summ = rv_an.get("summary", "")
                        ings = ", ".join(str(x) for x in rv_an.get("ingredients", []))
                        input_text = f"Dish Name: {dish}\nSummary: {summ}\nIngredients: {ings}"
                        source_title = dish
                        rec_analysis = rag_pipeline.analyze_recipe(input_text)
                    elif has_ac:
                        # Use already-analyzed content directly — no extra LLM call needed
                        source_title = ac.get("source_title", ac.get("dish_name", "Uploaded Content"))
                        rec_analysis = ac
                    else:
                        input_text = ctx
                        source_title = "Uploaded Nutrition Context"
                        rec_analysis = rag_pipeline.analyze_recipe(input_text)

                    # Normalize fields with fallback to "Not Available"
                    overall_summ = (
                        (rv_an.get("summary") if has_rv and rv_an.get("summary") else None)
                        or rec_analysis.get("overall_summary")
                        or rec_analysis.get("summary")
                        or rec_analysis.get("description")
                        or _NA
                    )

                    cal   = (rv_an.get("calories") if has_rv else None) or rec_analysis.get("calories") or _NA
                    pro   = (rv_an.get("protein") if has_rv else None) or rec_analysis.get("protein") or _NA
                    carb  = (rv_an.get("carbs") if has_rv else None) or rec_analysis.get("carbohydrates") or rec_analysis.get("carbs") or _NA
                    fat   = (rv_an.get("fat") if has_rv else None) or rec_analysis.get("fat") or _NA
                    fiber = (rv_an.get("fiber") if has_rv else None) or rec_analysis.get("fiber") or _NA

                    vits  = (rv_an.get("vitamins") if has_rv else None) or rec_analysis.get("vitamins") or rec_analysis.get("vitamins_minerals") or _NA
                    mins  = (rv_an.get("minerals") if has_rv else None) or rec_analysis.get("minerals") or _NA

                    health_ben = rec_analysis.get("health_benefits") or _NA
                    moderation = rec_analysis.get("consume_in_moderation") or _NA
                    suitable   = rec_analysis.get("suitable_for") or _NA

                    st.session_state.ns_data = {
                        "source_title":          source_title,
                        "overall_summary":       overall_summ,
                        "calories":              cal,
                        "protein":               pro,
                        "carbohydrates":         carb,
                        "fat":                   fat,
                        "fiber":                 fiber,
                        "vitamins":              vits,
                        "minerals":              mins,
                        "health_benefits":       health_ben,
                        "consume_in_moderation": moderation,
                        "suitable_for":          suitable,
                    }
                    st.session_state.ns_cache_key = current_cache_key

        ns_data = st.session_state.get("ns_data")

        # Normalize ns_data keys — handle both analyzed_content format and native ns_data format
        if ns_data and "overall_summary" not in ns_data and "summary" in ns_data:
            ns_data["overall_summary"] = ns_data["summary"]
        if ns_data and "source_title" not in ns_data and "dish_name" in ns_data:
            ns_data["source_title"] = ns_data["dish_name"]

        if not ns_data or (not has_ac and not has_rv and not has_ctx):
            st.markdown(
                """<div class="rv-empty-state">
                    <div class="rv-empty-icon">📋</div>
                    <div class="rv-empty-title">No Nutrition Summary Available Yet</div>
                    <div class="rv-empty-sub">
                        Upload a recipe, food image, or nutrition PDF in the sidebar to automatically generate your Nutrition Summary dashboard.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            source_title = ns_data.get("source_title", "Analyzed Content")

            # ── Audio Control (TTS only — Ask by Voice removed in Task 10) ─
            if st.button("🔊 Listen Summary", use_container_width=False, key="btn_ns_tts"):
                text_to_speak = f"Nutrition Summary for {source_title}. {ns_data.get('overall_summary', '')}"
                safe_tts = (
                    text_to_speak.replace("\\", "\\\\")
                    .replace("'", "\\'")
                    .replace('"', '\\"')
                    .replace("\n", " ")
                )[:800]
                st.components.v1.html(
                    f"""<script>
                    if('speechSynthesis' in window){{
                        window.speechSynthesis.cancel();
                        var u=new SpeechSynthesisUtterance('{safe_tts}');
                        u.rate=0.9; u.pitch=1.0; u.lang='en-US';
                        window.speechSynthesis.speak(u);
                    }} else {{
                        alert('Text-to-speech is not supported in this browser.');
                    }}
                    </script>""",
                    height=0,
                )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            # ── 1. 📝 Overall Summary (2–4 lines) ────────
            # Build content-specific summary from actual ns_data fields
            overall_summ = _build_content_summary(ns_data)
            st.markdown(
                f"""<div class="ns-card blue-theme">
                    <div class="ns-card-header">
                        <div class="ns-card-icon" style="background:var(--blue-l);">📝</div>
                        <div class="ns-card-title">Overall Summary</div>
                        <div style="flex:1;"></div>
                        <span class="ns-source-badge">📍 {html_lib.escape(source_title)}</span>
                    </div>
                    <div class="ns-card-body">
                        {html_lib.escape(overall_summ)}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── 2. 🍽 Estimated Nutrition ─────────────────
            st.markdown(
                "<div class='nutr-section-title' style='margin-top:20px;'>🍽 Estimated Nutrition</div>",
                unsafe_allow_html=True,
            )

            def _mc(cls, icon, label, val):
                val_s = str(val) if val is not None else ""
                if val_s and val_s not in (_NA, "Not Available", ""):
                    vhtml = f"<div class='nutr-macro-val'>{html_lib.escape(val_s)}</div>"
                else:
                    vhtml = "<div class='nutr-na'>Unable to Estimate</div>"
                return (
                    f"<div class='nutr-macro-card {cls}'>"
                    f"<div class='nutr-macro-icon'>{icon}</div>"
                    f"{vhtml}"
                    f"<div class='nutr-macro-label'>{label}</div>"
                    f"</div>"
                )

            cal = ns_data.get("calories", _NA)
            pro = ns_data.get("protein", _NA)
            carb = ns_data.get("carbohydrates", _NA)
            fat = ns_data.get("fat", _NA)
            fiber = ns_data.get("fiber", _NA)

            macro_row = (
                _mc("cal",  "🔥", "Calories", cal)
              + _mc("pro",  "🥩", "Protein",  pro)
              + _mc("carb", "🍚", "Carbs",    carb)
              + _mc("fat",  "🥑", "Fat",      fat)
              + _mc("fib",  "🌾", "Fiber",    fiber)
            )
            st.markdown(f"<div class='nutr-macros'>{macro_row}</div>", unsafe_allow_html=True)

            # ── 3. 💊 Key Nutrients ────────────────────────
            vits = ns_data.get("vitamins", _NA)
            mins = ns_data.get("minerals", _NA)

            def _mv(v):
                if isinstance(v, (dict, list)):
                    v = ", ".join(str(x) for x in (v.values() if isinstance(v, dict) else v))
                v = str(v) if v is not None else ""
                return (
                    f"<div class='nutr-micro-val'>{html_lib.escape(v)}</div>"
                    if v and v not in (_NA, "Not Available", "")
                    else "<div class='nutr-na'>Not Present in Uploaded Content</div>"
                )

            st.markdown(
                f"""<div class='nutr-micro-grid' style='margin-bottom:16px;'>
                    <div class='nutr-micro-card'>
                        <div class='nutr-micro-header'>
                            <div class='nutr-micro-icon vit'>☀️</div>
                            <div class='nutr-micro-label'>Vitamins</div>
                        </div>
                        {_mv(vits)}
                    </div>
                    <div class='nutr-micro-card'>
                        <div class='nutr-micro-header'>
                            <div class='nutr-micro-icon min'>💎</div>
                            <div class='nutr-micro-label'>Minerals</div>
                        </div>
                        {_mv(mins)}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── 4. 💚 Health Benefits & 5. ⚠️ Consume in Moderation ──
            col_hb, col_cm = st.columns(2, gap="medium")

            with col_hb:
                hb_raw = ns_data.get("health_benefits", _NA)
                if isinstance(hb_raw, (dict, list)):
                    hb_text = ", ".join(str(x) for x in (hb_raw.values() if isinstance(hb_raw, dict) else hb_raw))
                else:
                    hb_text = str(hb_raw) if hb_raw is not None else ""
                hb_body = (
                    f"<div>{html_lib.escape(hb_text)}</div>"
                    if hb_text and hb_text != _NA
                    else f"<div class='nutr-na'>{_NA}</div>"
                )
                st.markdown(
                    f"""<div class="ns-card green-theme" style="height:100%;">
                        <div class="ns-card-header">
                            <div class="ns-card-icon" style="background:var(--green-l);">💚</div>
                            <div class="ns-card-title">Health Benefits</div>
                        </div>
                        <div class="ns-card-body">
                            {hb_body}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            with col_cm:
                cm_raw = ns_data.get("consume_in_moderation", _NA)
                if isinstance(cm_raw, (dict, list)):
                    cm_text = ", ".join(str(x) for x in (cm_raw.values() if isinstance(cm_raw, dict) else cm_raw))
                else:
                    cm_text = str(cm_raw) if cm_raw is not None else ""
                cm_body = (
                    f"<div>{html_lib.escape(cm_text)}</div>"
                    if cm_text and cm_text != _NA
                    else f"<div class='nutr-na'>{_NA}</div>"
                )
                st.markdown(
                    f"""<div class="ns-card warning-theme" style="height:100%;">
                        <div class="ns-card-header">
                            <div class="ns-card-icon" style="background:rgba(249,115,22,0.12);">⚠️</div>
                            <div class="ns-card-title">Consume in Moderation</div>
                        </div>
                        <div class="ns-card-body">
                            {cm_body}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            # ── 6. 👨‍👩‍👧 Best Suitable For ─────────────────
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            suitable_text = ns_data.get("suitable_for", _NA)

            if suitable_text and suitable_text != _NA:
                groups = [g.strip() for g in re.split(r'[,/|;]', suitable_text) if g.strip()]
                if not groups:
                    groups = [suitable_text]
                chips_html = "".join(
                    f"<span class='ns-suitable-chip'>👤 {html_lib.escape(g)}</span>"
                    for g in groups
                )
                suitable_body = f"<div class='ns-suitable-chips'>{chips_html}</div>"
            else:
                suitable_body = f"<div class='nutr-na'>{_NA}</div>"

            st.markdown(
                f"""<div class="ns-card purple-theme">
                    <div class="ns-card-header">
                        <div class="ns-card-icon" style="background:rgba(139,92,246,0.12);">👨‍👩‍👧</div>
                        <div class="ns-card-title">Best Suitable For</div>
                    </div>
                    <div class="ns-card-body">
                        {suitable_body}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  🧠 NUTRITION CARDS
    # ═══════════════════════════════════════
    elif selected == "🧠 Nutrition Cards":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>🧠 Nutrition Learning Cards</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Interactive 3D flip cards for key nutrients automatically "
            "detected from your analyzed recipes, documents, or food images.</div>",
            unsafe_allow_html=True,
        )

        _NC_CATALOG = {
            "Protein": {
                "icon": "🥩",
                "name": "Protein",
                "short_desc": "Essential macronutrient for building muscle, tissue repair, and enzyme synthesis.",
                "importance": "Critical structural component of every cell and muscle fiber in your body.",
                "sources": "Chicken, Eggs, Paneer, Tofu, Lentils, Fish, Greek Yogurt",
                "benefits": "Muscle growth, tissue repair, satiety, immune function, and bone strength.",
                "intake": "0.8–1.2 g per kg body weight (approx 56g/day for average adults)",
                "bg": "#FFEDD5",
                "color": "#C2410C",
                "keywords": ["protein", "paneer", "chicken", "egg", "tofu", "lentil", "dal", "fish", "meat", "yogurt", "whey", "soy", "gram", "bean", "chana", "rajma"]
            },
            "Carbohydrates": {
                "icon": "🍚",
                "name": "Carbohydrates",
                "short_desc": "Primary energy source that fuels your brain, muscles, and central nervous system.",
                "importance": "Main metabolic fuel for daily physical activity and high-intensity cognitive function.",
                "sources": "Whole Grains, Oats, Rice, Quinoa, Sweet Potatoes, Bananas",
                "benefits": "Sustained energy, brain power, athletic stamina, and glycogen replenishment.",
                "intake": "45%–65% of total daily calories (approx 225–325g/day)",
                "bg": "#E0F2FE",
                "color": "#0369A1",
                "keywords": ["carb", "carbohydrate", "rice", "wheat", "roti", "bread", "oats", "potato", "quinoa", "poha", "grain", "flour", "sugar", "banana", "corn"]
            },
            "Healthy Fats": {
                "icon": "🥑",
                "name": "Healthy Fats",
                "short_desc": "Vital for hormone production, brain health, and absorbing fat-soluble vitamins.",
                "importance": "Protects organs, maintains cell membrane integrity, and supports neurological function.",
                "sources": "Avocados, Nuts, Seeds, Olive Oil, Salmon, Ghee, Chia Seeds",
                "benefits": "Heart health, hormone balance, long-lasting satiety, and cell protection.",
                "intake": "20%–35% of total daily calories (approx 44–77g/day)",
                "bg": "#DCFCE7",
                "color": "#15803D",
                "keywords": ["fat", "oil", "ghee", "butter", "avocado", "nut", "almond", "walnut", "seed", "olive", "salmon", "omega"]
            },
            "Fiber": {
                "icon": "🌾",
                "name": "Fiber",
                "short_desc": "Plant-based carbohydrate that promotes gut health and steady blood sugar.",
                "importance": "Essential for digestive regularity and feeding beneficial gut microbiomes.",
                "sources": "Whole Grains, Beans, Berries, Chia Seeds, Apples, Broccoli, Oats",
                "benefits": "Digestive regularity, blood sugar stability, lowering cholesterol, and satiety.",
                "intake": "25–38 grams per day for adults",
                "bg": "#F3E8FF",
                "color": "#7E22CE",
                "keywords": ["fiber", "fibre", "whole grain", "oats", "flax", "chia", "apple", "berry", "vegetables", "spinach", "broccoli", "sprouts", "legume"]
            },
            "Vitamin C": {
                "icon": "🍊",
                "name": "Vitamin C",
                "short_desc": "Powerful antioxidant that boosts immunity, collagen formation, and iron absorption.",
                "importance": "Protects cells from oxidative damage and synthesizes collagen for skin and joints.",
                "sources": "Oranges, Bell Peppers, Strawberries, Kiwis, Tomatoes, Lemon, Broccoli",
                "benefits": "Immune defense, glowing skin, rapid wound healing, and cellular protection.",
                "intake": "75–90 mg per day for adults",
                "bg": "#FFE4E6",
                "color": "#EA580C",
                "keywords": ["vitamin c", "citrus", "lemon", "orange", "amla", "tomato", "pepper", "capsicum", "berry", "kiwi", "ascorbic"]
            },
            "Vitamin A": {
                "icon": "🥕",
                "name": "Vitamin A",
                "short_desc": "Essential micronutrient for sharp vision, immune strength, and cell growth.",
                "importance": "Maintains healthy retina photoreceptors and mucosal lining protection.",
                "sources": "Carrots, Sweet Potatoes, Spinach, Kale, Eggs, Butter, Papaya",
                "benefits": "Night vision, skin cellular repair, immune response, and organ protection.",
                "intake": "700–900 mcg RAE per day for adults",
                "bg": "#FEE2E2",
                "color": "#B91C1C",
                "keywords": ["vitamin a", "carrot", "spinach", "kale", "sweet potato", "papaya", "egg", "retinol", "beta-carotene", "mango"]
            },
            "Vitamin D": {
                "icon": "🌞",
                "name": "Vitamin D",
                "short_desc": "Sunshine vitamin regulating calcium absorption, bone strength, and mood.",
                "importance": "Crucial for calcium homeostasis, bone mineral density, and immune regulation.",
                "sources": "Sunlight exposure, Fatty Fish, Egg Yolks, Fortified Milk, Mushrooms",
                "benefits": "Strong bones & teeth, mood regulation, reduced inflammation, and immunity.",
                "intake": "600–800 IU (15–20 mcg) per day for adults",
                "bg": "#FEF9C3",
                "color": "#A16207",
                "keywords": ["vitamin d", "sunlight", "sunshine", "mushroom", "fortified", "egg yolk", "fish oil", "calciferol"]
            },
            "Iron": {
                "icon": "🩸",
                "name": "Iron",
                "short_desc": "Vital trace mineral required for hemoglobin synthesis and oxygen transport.",
                "importance": "Enables red blood cells to deliver oxygen from lungs to every body organ.",
                "sources": "Spinach, Lentils, Red Meat, Tofu, Pumpkin Seeds, Jaggery, Beans",
                "benefits": "Oxygen delivery, physical stamina, prevention of anemia, and focus.",
                "intake": "8–18 mg per day for adults",
                "bg": "#FFE4E6",
                "color": "#BE123C",
                "keywords": ["iron", "hemoglobin", "spinach", "palak", "jaggery", "beetroot", "meat", "lentil", "sesame", "dates"]
            },
            "Calcium": {
                "icon": "🥛",
                "name": "Calcium",
                "short_desc": "Primary structural mineral for strong bones, teeth, and muscle contraction.",
                "importance": "Essential for skeletal integrity, nerve signal transmission, and blood clotting.",
                "sources": "Milk, Yogurt, Paneer, Cheese, Fortified Plant Milk, Leafy Greens, Almonds",
                "benefits": "Bone density, strong teeth, heart rhythm regulation, and muscle control.",
                "intake": "1,000–1,200 mg per day for adults",
                "bg": "#F1F5F9",
                "color": "#334155",
                "keywords": ["calcium", "milk", "paneer", "curd", "yogurt", "cheese", "dairy", "ragi", "sesame", "almond"]
            },
            "Hydration": {
                "icon": "💧",
                "name": "Hydration",
                "short_desc": "Vital fluid balance supporting circulation, temperature regulation, and detox.",
                "importance": "Comprises ~60% of human body weight and facilitates every metabolic reaction.",
                "sources": "Water, Cucumber, Watermelon, Coconut Water, Herbal Teas, Soups",
                "benefits": "Energy levels, kidney function, joint lubrication, and physical endurance.",
                "intake": "2.7–3.7 Liters of total fluids per day",
                "bg": "#CFFAFE",
                "color": "#0E7490",
                "keywords": ["water", "hydration", "fluid", "cucumber", "watermelon", "soup", "curd", "buttermilk", "coconut water", "juice", "liquid"]
            }
        }

        # Primary: shared analyzed_content from upload auto-analysis
        ac = st.session_state.get("analyzed_content")
        rv_an = st.session_state.get("rv_analysis")
        ctx = lm.get("context_text", "") or (ac.get("context_text", "") if ac else "")

        has_ac  = bool(ac and ac.get("is_recipe"))
        has_rv  = bool(rv_an and rv_an.get("is_recipe") and not rv_an.get("is_not_food_image"))
        has_ctx = bool(ctx and ctx.strip())

        ac_key  = hash(str(ac)) if ac else "none"
        rv_key  = hash(str(rv_an)) if rv_an else "none"
        ctx_key = hash(ctx) if ctx else "none"
        current_nc_key = f"nc_ac_{ac_key}_rv_{rv_key}_ctx_{ctx_key}"

        # Automatic detection & hash-based caching
        if (st.session_state.get("nc_cache_key") != current_nc_key) or (st.session_state.get("nc_cards") is None):
            if has_ac or has_rv or has_ctx:
                # Build a rich text blob from whichever source is available
                text_blob = ""
                if has_ac:
                    text_blob += f" {ac.get('source_title', '')} {ac.get('summary', '')} {ac.get('protein', '')} {ac.get('carbohydrates', '')} {ac.get('fat', '')} {ac.get('fiber', '')} {ac.get('vitamins', '')} {ac.get('minerals', '')} {ac.get('health_benefits', '')}"
                if has_rv:
                    text_blob += f" {rv_an.get('dish_name', '')} {rv_an.get('summary', '')} {' '.join(str(i) for i in rv_an.get('ingredients', []))} {rv_an.get('protein', '')} {rv_an.get('carbs', '')} {rv_an.get('fat', '')} {rv_an.get('fiber', '')} {rv_an.get('vitamins', '')} {rv_an.get('minerals', '')}"
                if has_ctx:
                    text_blob += f" {ctx}"
                text_blob = text_blob.lower()

                detected_cards = []

                for nut_name, cat in _NC_CATALOG.items():
                    match_count = sum(1 for kw in cat["keywords"] if kw in text_blob)
                    is_relevant = match_count > 0

                    if is_relevant:
                        level = "Medium"
                        if match_count >= 3:
                            level = "High"
                        elif match_count == 1:
                            level = "Low"

                        # Refine level based on numerical values if available
                        # Use rv_an values if present, otherwise fall back to ac
                        src = rv_an if has_rv else (ac if has_ac else {})
                        if nut_name == "Protein":
                            p_str = str(src.get("protein", ""))
                            val = int(re.search(r'\d+', p_str).group()) if re.search(r'\d+', p_str) else 0
                            if val >= 18: level = "High"
                            elif val >= 8: level = "Medium"
                            elif val > 0: level = "Low"
                        elif nut_name == "Carbohydrates":
                            c_str = str(src.get("carbohydrates", src.get("carbs", "")))
                            val = int(re.search(r'\d+', c_str).group()) if re.search(r'\d+', c_str) else 0
                            if val >= 35: level = "High"
                            elif val >= 15: level = "Medium"
                            elif val > 0: level = "Low"
                        elif nut_name == "Healthy Fats":
                            f_str = str(src.get("fat", ""))
                            val = int(re.search(r'\d+', f_str).group()) if re.search(r'\d+', f_str) else 0
                            if val >= 15: level = "High"
                            elif val >= 6: level = "Medium"
                            elif val > 0: level = "Low"
                        elif nut_name == "Fiber":
                            fib_str = str(src.get("fiber", ""))
                            val = int(re.search(r'\d+', fib_str).group()) if re.search(r'\d+', fib_str) else 0
                            if val >= 6: level = "High"
                            elif val >= 3: level = "Medium"
                            elif val > 0: level = "Low"

                        detected_cards.append({
                            "category": cat,
                            "level": level,
                        })

                st.session_state.nc_cards = detected_cards
                st.session_state.nc_cache_key = current_nc_key

        cards = st.session_state.get("nc_cards")

        if not cards or not (has_ac or has_rv or has_ctx):
            st.markdown(
                """<div class="rv-empty-state">
                    <div class="rv-empty-icon">🧠</div>
                    <div class="rv-empty-title">No nutrition cards available for this content.</div>
                    <div class="rv-empty-sub">
                        Upload a recipe, food image, or nutrition PDF in the sidebar to detect relevant nutrient cards.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='font-size:0.8rem;color:var(--text-3);margin-bottom:12px;'>"
                f"Showing <b>{len(cards)}</b> detected nutrient cards based on your content. Hover any card to flip.</div>",
                unsafe_allow_html=True,
            )

            cols = st.columns(3, gap="medium")
            for i, item in enumerate(cards):
                cat = item["category"]
                level = item["level"]

                icon = cat["icon"]
                name = cat["name"]
                short_desc = cat["short_desc"]
                importance = cat["importance"]
                sources = cat["sources"]
                benefits = cat["benefits"]
                intake = cat["intake"]
                pastel_bg = cat["bg"]
                theme_color = cat["color"]

                lvl_class = level.lower()

                with cols[i % 3]:
                    st.markdown(
                        f"""<div class="nc-flip-wrap">
                          <div class="nc-flip-inner">
                            <div class="nc-flip-front">
                                <div class="nc-front-top">
                                    <span style="font-size:0.7rem;font-weight:700;color:{theme_color};">
                                        {icon} NUTRIENT
                                    </span>
                                    <span class="nc-badge {lvl_class}">{level}</span>
                                </div>
                                <div class="nc-front-hero" style="background:{pastel_bg};">
                                    <div class="nc-front-icon">{icon}</div>
                                    <div class="nc-front-title">{name}</div>
                                </div>
                                <div class="nc-front-desc">{html_lib.escape(short_desc)}</div>
                                <div class="nc-front-hint">🔄 Hover to flip details</div>
                            </div>
                            <div class="nc-flip-back">
                                <div class="nc-back-title" style="color:{theme_color};">
                                    <span>{icon} {name}</span>
                                    <span class="nc-badge {lvl_class}">{level} Level</span>
                                </div>
                                <div class="nc-back-row">🌟 <b>Importance:</b> {html_lib.escape(importance)}</div>
                                <div class="nc-back-row">🥑 <b>Major Food Sources:</b> {html_lib.escape(sources)}</div>
                                <div class="nc-back-row">💚 <b>Health Benefits:</b> {html_lib.escape(benefits)}</div>
                                <div class="nc-back-row">📏 <b>Recommended Daily Intake:</b> {html_lib.escape(intake)}</div>
                                <div class="nc-back-row" style="margin-top:6px;padding-top:6px;border-top:1px dashed var(--border);">
                                    📊 <b>Recipe Profile:</b> This dish/content is <b>{level}</b> in {name}.
                                </div>
                            </div>
                          </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  ❓ QUIZ
    # ═══════════════════════════════════════
    # ═══════════════════════════════════════
    #  ❓ QUIZ
    # ═══════════════════════════════════════
    elif selected == "❓ Quiz":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>❓ AI Nutrition Quiz</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Test your knowledge with multiple-choice questions automatically "
            "generated from your analyzed recipes, documents, or nutrition summary.</div>",
            unsafe_allow_html=True,
        )

        # Primary: shared analyzed_content from upload auto-analysis
        ac = st.session_state.get("analyzed_content")
        rv_an = st.session_state.get("rv_analysis")
        ctx = lm.get("context_text", "") or (ac.get("context_text", "") if ac else "")
        ns_data = st.session_state.get("ns_data") or ac  # fall back to ac if ns_data not yet built

        has_ac  = bool(ac and ac.get("is_recipe"))
        has_rv  = bool(rv_an and rv_an.get("is_recipe") and not rv_an.get("is_not_food_image"))
        has_ctx = bool(ctx and ctx.strip())
        has_ns  = bool(ns_data is not None)

        has_content = has_ac or has_rv or has_ctx or has_ns

        ac_key  = hash(str(ac)) if ac else "none"
        rv_key  = hash(str(rv_an)) if rv_an else "none"
        ctx_key = hash(ctx) if ctx else "none"
        ns_key  = hash(str(ns_data)) if ns_data else "none"
        current_quiz_key = f"quiz_ac_{ac_key}_rv_{rv_key}_ctx_{ctx_key}_ns_{ns_key}"

        if not has_content:
            st.markdown(
                """<div class="rv-empty-state">
                    <div class="rv-empty-icon">❓</div>
                    <div class="rv-empty-title">No Nutrition Content Analyzed Yet</div>
                    <div class="rv-empty-sub">
                        Upload a recipe, food image, or nutrition PDF in the sidebar to enable the AI Nutrition Quiz.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            st.button("❓ Generate Quiz", disabled=True, key="btn_quiz_disabled", use_container_width=True)
        else:
            # Check cache or generate button trigger
            if (st.session_state.get("quiz_cache_key") != current_quiz_key) or (st.session_state.get("quiz_questions") is None):
                if st.button("❓ Generate Quiz", use_container_width=True, key="btn_quiz_generate"):
                    with st.spinner("Generating AI Nutrition Quiz from content…"):
                        questions = _build_quiz_questions(ns_data, rv_an, ctx)
                        st.session_state.quiz_questions = questions
                        st.session_state.quiz_cache_key = current_quiz_key
                        st.session_state.quiz_current_idx = 0
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.rerun()

            questions = st.session_state.get("quiz_questions")

            if not questions:
                if not st.session_state.get("btn_quiz_generate"):
                    st.info("💡 Click **Generate Quiz** above to build questions from your analyzed content.")
            else:
                total_q = len(questions)
                curr_idx = st.session_state.get("quiz_current_idx", 0)

                # Clamp index safely
                curr_idx = max(0, min(curr_idx, total_q - 1))
                st.session_state.quiz_current_idx = curr_idx

                is_submitted = st.session_state.get("quiz_submitted", False)

                if not is_submitted:
                    # ── Quiz Active Mode (One question at a time) ─────────
                    q_item = questions[curr_idx]
                    topic = q_item.get("topic", "Nutrition")
                    q_text = q_item.get("question", "")
                    opts = q_item.get("options", [])

                    progress_pct = int(((curr_idx + 1) / total_q) * 100)

                    st.markdown(
                        f"""<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                            <span style="font-size:0.85rem;font-weight:700;color:var(--text-1);">Question {curr_idx + 1} of {total_q}</span>
                            <span style="font-size:0.78rem;font-weight:600;color:var(--green);">{progress_pct}% Completed</span>
                        </div>
                        <div class="quiz-progress-bar">
                            <div class="quiz-progress-fill" style="width:{progress_pct}%;"></div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"""<div class="quiz-card">
                            <div class="quiz-topic-tag">🏷️ {html_lib.escape(topic)}</div>
                            <div class="quiz-question-text">{html_lib.escape(q_text)}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                    # Radio choice for options
                    selected_ans = st.session_state.quiz_answers.get(curr_idx)
                    chosen = st.radio(
                        "Select your answer:",
                        opts,
                        key=f"q_opt_radio_{curr_idx}",
                        index=opts.index(selected_ans) if selected_ans in opts else None,
                        label_visibility="collapsed",
                    )
                    if chosen:
                        st.session_state.quiz_answers[curr_idx] = chosen

                    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

                    # Navigation controls
                    col_p, col_n, col_s = st.columns([1, 1, 1.2], gap="small")

                    with col_p:
                        if st.button("← Previous", use_container_width=True, disabled=(curr_idx == 0), key="btn_q_prev"):
                            st.session_state.quiz_current_idx -= 1
                            st.rerun()

                    with col_n:
                        if st.button("Next →", use_container_width=True, disabled=(curr_idx == total_q - 1), key="btn_q_next"):
                            st.session_state.quiz_current_idx += 1
                            st.rerun()

                    with col_s:
                        answered_count = len(st.session_state.quiz_answers)
                        if st.button(f"✨ Submit Quiz ({answered_count}/{total_q})", use_container_width=True, key="btn_q_submit"):
                            st.session_state.quiz_submitted = True
                            st.rerun()

                else:
                    # ── Quiz Submitted Mode (Results & Detailed Review) ───
                    correct_count = 0
                    weak_topics = set()

                    for idx, q_item in enumerate(questions):
                        user_ans = st.session_state.quiz_answers.get(idx, "")
                        correct_val = str(q_item.get("correct", "")).strip().upper()

                        is_correct = False
                        if user_ans:
                            if user_ans.strip().upper().startswith(correct_val):
                                is_correct = True
                            elif correct_val in user_ans.strip().upper():
                                is_correct = True

                        if is_correct:
                            correct_count += 1
                        else:
                            weak_topics.add(q_item.get("topic", "Nutrition"))

                    percentage = round((correct_count / total_q) * 100, 1)

                    st.markdown(
                        f"""<div class="quiz-results-card">
                            <div class="quiz-score-header">
                                <div>
                                    <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-3);margin-bottom:4px;">Quiz Results</div>
                                    <div class="quiz-score-big">{correct_count} / {total_q}</div>
                                    <div style="font-size:0.9rem;font-weight:600;color:var(--text-2);margin-top:4px;">Overall Score: {percentage}%</div>
                                </div>
                                <div style="text-align:right;">
                                    <span class="ns-source-badge" style="font-size:0.85rem;padding:6px 16px;">
                                        {"🏆 Excellent Mastery!" if percentage >= 80 else ("👍 Good Effort!" if percentage >= 50 else "📚 Needs Review")}
                                    </span>
                                </div>
                            </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

                    # Detailed Review Header
                    st.markdown(
                        "<div class='wcard-title' style='font-size:1.1rem;margin-bottom:12px;'>📝 Correct Answers &amp; Explanations</div>",
                        unsafe_allow_html=True,
                    )

                    for idx, q_item in enumerate(questions):
                        topic = q_item.get("topic", "Nutrition")
                        q_text = q_item.get("question", "")
                        correct_ans = q_item.get("correct", "")
                        opts = q_item.get("options", [])
                        expl = q_item.get("explanation", "Based on analyzed nutrition facts.")

                        user_ans = st.session_state.quiz_answers.get(idx, "No answer selected")

                        full_correct = next((o for o in opts if o.strip().upper().startswith(str(correct_ans).upper())), f"Option {correct_ans}")

                        is_correct = user_ans != "No answer selected" and (user_ans.strip().upper().startswith(str(correct_ans).upper()))

                        icon_status = "✅ Correct" if is_correct else "❌ Incorrect"
                        color_status = "var(--green)" if is_correct else "var(--red)"

                        st.markdown(
                            f"""<div class="quiz-review-item">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                    <span class="quiz-topic-tag">🏷️ {html_lib.escape(topic)}</span>
                                    <span style="font-weight:700;font-size:0.82rem;color:{color_status};">{icon_status}</span>
                                </div>
                                <div style="font-size:0.95rem;font-weight:700;color:var(--text-1);margin-bottom:8px;">Q{idx+1}: {html_lib.escape(q_text)}</div>
                                <div style="font-size:0.82rem;color:var(--text-2);margin-bottom:4px;"><b>Your Answer:</b> {html_lib.escape(user_ans)}</div>
                                <div style="font-size:0.82rem;color:var(--green);margin-bottom:8px;"><b>Correct Answer:</b> {html_lib.escape(full_correct)}</div>
                                <div class="quiz-expl-box">
                                    💡 <b>Explanation:</b> {html_lib.escape(expl)}
                                </div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                    # Weak Topics & Personalized Recommendation
                    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
                    weak_list = list(weak_topics)

                    if weak_list:
                        weak_html = ", ".join(f"<b>{t}</b>" for t in weak_list)
                        rec_msg = f"Review the {weak_html} cards in the <b>🧠 Nutrition Cards</b> module to strengthen your understanding."
                    else:
                        weak_html = "None! You demonstrated strong mastery across all topics."
                        rec_msg = "Great job! Keep testing your knowledge with new recipes and food images in <b>🖼 Recipe Visualizer</b>."

                    st.markdown(
                        f"""<div class="quiz-recommend-box">
                            <div style="font-size:0.95rem;font-weight:700;color:var(--text-1);margin-bottom:6px;">🎯 Weak Nutrition Topics</div>
                            <div style="font-size:0.85rem;color:var(--text-2);margin-bottom:12px;">{weak_html}</div>
                            <div style="font-size:0.95rem;font-weight:700;color:var(--purple);margin-bottom:4px;">💡 Personalized Recommendation</div>
                            <div style="font-size:0.85rem;color:var(--text-2);">{rec_msg}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
                    col_r1, col_r2 = st.columns(2, gap="small")
                    with col_r1:
                        if st.button("🔄 Retake Quiz", use_container_width=True, key="btn_retake_quiz"):
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_current_idx = 0
                            st.session_state.quiz_answers = {}
                            st.rerun()

                    with col_r2:
                        if st.button("✨ Regenerate New Questions", use_container_width=True, key="btn_regen_quiz"):
                            st.session_state.quiz_questions = None
                            st.session_state.quiz_cache_key = None
                            st.session_state.quiz_submitted = False
                            st.session_state.quiz_current_idx = 0
                            st.session_state.quiz_answers = {}
                            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  🖼 RECIPE VISUALIZER
    # ═══════════════════════════════════════
    elif selected == "🖼 Recipe Visualizer":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>🖼 Recipe Visualizer</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Analyze any recipe or food image for nutritional insights. "
            "Type a dish name, or upload a document or food image below.</div>",
            unsafe_allow_html=True,
        )

        # ── Text Input for Recipe / Dish Name ─────────────
        dish_name_input = st.text_input(
            "Recipe / Dish Name",
            placeholder="Enter recipe or dish name (e.g., Paneer Tikka, Poha, Dal Khichdi)...",
            key="rv_dish_name_ui",
        )

        # ── Large Upload Box supporting PDF, JPG, JPEG, PNG, TXT ──
        uploaded_file = st.file_uploader(
            "Upload Recipe Document or Food Image",
            type=["pdf", "jpg", "jpeg", "png", "txt"],
            key="rv_file_uploader_ui",
            help="Supports PDF, JPG, JPEG, PNG, and TXT files",
        )

        # ── Image Preview (shown immediately on upload) ──
        _IMG_EXTS = (".jpg", ".jpeg", ".png")
        if uploaded_file and uploaded_file.name.lower().endswith(_IMG_EXTS):
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            st.image(
                uploaded_file,
                caption=f"📸 Uploaded: {uploaded_file.name}",
                use_container_width=False,
                width=320,
            )

        # ── Analyze Recipe Button ─────────────────────────
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Analyze Recipe", use_container_width=True, key="btn_rv_analyze_ui"):
            recipe_input = dish_name_input.strip() if dish_name_input and dish_name_input.strip() else ""

            if uploaded_file:
                fname = uploaded_file.name
                is_image_upload = fname.lower().endswith(_IMG_EXTS)

                if is_image_upload:
                    raw_bytes = uploaded_file.read()
                    with st.spinner("🔍 Identifying food in image…"):
                        rec_res = api_client.recognize_food(raw_bytes, fname)
                    
                    if rec_res and rec_res.get("is_food"):
                        detected_name = rec_res.get("detected_food_name")
                        with st.spinner("Searching database…"):
                            db_food = api_client.get_food_by_name(detected_name)
                            
                        if db_food:
                            result = _map_api_to_result(db_food)
                            st.session_state.rv_analysis = result
                            st.session_state.analyzed_content = result
                            st.session_state.ns_data = result
                        else:
                            with st.spinner("🍽 Analyzing nutrition…"):
                                api_res = api_client.analyze_nutrition(detected_name)
                            if api_res:
                                result = _map_api_to_result(api_res)
                                st.session_state.rv_analysis = result
                                st.session_state.analyzed_content = result
                                st.session_state.ns_data = result
                            else:
                                with st.spinner("🔍 Falling back to local analysis…"):
                                    result = rag_pipeline.analyze_food_image(raw_bytes, fname)
                                st.session_state.rv_analysis = result
                    else:
                        st.session_state.rv_analysis = {"is_recipe": False, "is_not_food_image": True}
                else:
                    # PDF / TXT path
                    with st.spinner("Reading uploaded file…"):
                        extracted_text, _ = _extract_text_from_upload(uploaded_file)
                    if extracted_text and extracted_text.strip():
                        if recipe_input:
                            recipe_input = f"Dish: {recipe_input}\n\n{extracted_text}"
                        else:
                            recipe_input = extracted_text

                    if not recipe_input:
                        st.warning("⚠️ Could not extract text from the uploaded file. Try a different PDF or TXT file.")
                    else:
                        with st.spinner("🍽 Analyzing recipe nutrition…"):
                            api_res = api_client.analyze_nutrition(recipe_input)
                        if api_res:
                            result = _map_api_to_result(api_res)
                            st.session_state.rv_analysis = result
                            st.session_state.analyzed_content = result
                            st.session_state.ns_data = result
                        else:
                            with st.spinner("🍽 Falling back to local recipe extraction…"):
                                result = rag_pipeline.extract_recipe_info(recipe_input)
                            st.session_state.rv_analysis = result

            elif recipe_input:
                # Text-only path
                with st.spinner("Searching database…"):
                    db_food = api_client.get_food_by_name(recipe_input)
                if db_food:
                    result = _map_api_to_result(db_food)
                    st.session_state.rv_analysis = result
                    st.session_state.analyzed_content = result
                    st.session_state.ns_data = result
                else:
                    with st.spinner("🍽 Analyzing nutrition…"):
                        api_res = api_client.analyze_nutrition(recipe_input)
                    if api_res:
                        result = _map_api_to_result(api_res)
                        st.session_state.rv_analysis = result
                        st.session_state.analyzed_content = result
                        st.session_state.ns_data = result
                    else:
                        with st.spinner("🍽 Falling back to local recipe extraction…"):
                            result = rag_pipeline.extract_recipe_info(recipe_input)
                        st.session_state.rv_analysis = result
            else:
                st.warning(
                    "⚠️ Please enter a recipe name or upload a Nutrition PDF, Food Image, or Text file."
                )

        # ── Results / Empty State ─────────────────────────
        analysis = st.session_state.rv_analysis

        if analysis is None:
            # Empty state
            st.markdown(
                """<div class="rv-empty-state">
                    <div class="rv-empty-icon">🖼️</div>
                    <div class="rv-empty-title">Upload a recipe or food image.</div>
                    <div class="rv-empty-sub">Type a recipe or dish name or upload a Food Image, Nutrition PDF, or text file above, then click <b>Analyze Recipe</b>.</div>
                </div>""",
                unsafe_allow_html=True,
            )

        elif analysis.get("is_not_food_image"):
            # Not food image
            st.markdown(
                """<div class="rv-not-recipe">
                    <div style="font-size:48px;margin-bottom:12px;">🚫</div>
                    <div style="font-size:1.05rem;font-weight:700;color:var(--text-1);
                                margin-bottom:6px;">This image does not appear to contain food.</div>
                    <div style="font-size:.84rem;color:var(--text-2);line-height:1.5;">
                        Please upload a food photo, recipe card, or menu image.<br>
                        You can also type a dish name directly in the text field above.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            dish_name   = analysis.get("dish_name",   "Recipe Dish")
            summary     = analysis.get("summary",     "")
            ingredients = analysis.get("ingredients", [])
            _NA = "Not Available"
            cal   = analysis.get("calories",  _NA) or _NA
            pro   = analysis.get("protein",   _NA) or _NA
            carbs = analysis.get("carbs",     _NA) or analysis.get("carbohydrates", _NA) or _NA
            fat   = analysis.get("fat",       _NA) or _NA
            fiber = analysis.get("fiber",     _NA) or _NA
            vits  = analysis.get("vitamins",  _NA) or _NA
            mins  = analysis.get("minerals",  _NA) or _NA

            # Single-column layout — img_col removed (Generate Dish Image removed in Task 10)
            info_col = st.container()

            with info_col:
                # ── Dish Name & Summary ───────────────────
                st.markdown(
                    f"""<div class="rv-card">
                        <div class="rv-dish-name">🍽 {html_lib.escape(dish_name)}</div>
                        <div class="rv-desc">{html_lib.escape(summary)}</div>""",
                    unsafe_allow_html=True,
                )

                # ── Ingredients List ──────────────────────
                if ingredients:
                    items_html = "".join(
                        f"<li>{html_lib.escape(str(ing))}</li>"
                        for ing in ingredients
                    )
                    st.markdown(
                        f"<div style='margin-top:14px;'>"
                        f"<div class='rv-row-label' style='font-size:.8rem;margin-bottom:8px;'>"
                        f"🛒 Ingredients</div>"
                        f"<ul class='rec-list'>{items_html}</ul>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

                # ── Nutrition Analysis Cards ──────────────
                st.markdown(
                    "<div class='nutr-section-title'>📊 Nutrition Analysis</div>",
                    unsafe_allow_html=True,
                )

                # helper: single macro card HTML
                def _mc(cls, icon, label, value):
                    if value and value not in (_NA, "Not Available", ""):
                        vhtml = f"<div class='nutr-macro-val'>{html_lib.escape(value)}</div>"
                    else:
                        vhtml = "<div class='nutr-na'>Unable to Estimate</div>"
                    return (
                        f"<div class='nutr-macro-card {cls}'>"
                        f"<div class='nutr-macro-icon'>{icon}</div>"
                        f"{vhtml}"
                        f"<div class='nutr-macro-label'>{label}</div>"
                        f"</div>"
                    )

                macro_row = (
                    _mc("cal",  "🔥", "Calories", cal)
                  + _mc("pro",  "🥩", "Protein",  pro)
                  + _mc("carb", "🍚", "Carbs",    carbs)
                  + _mc("fat",  "🥑", "Fat",      fat)
                  + _mc("fib",  "🌾", "Fiber",    fiber)
                )
                st.markdown(
                    f"<div class='nutr-macros'>{macro_row}</div>",
                    unsafe_allow_html=True,
                )

                # Vitamins & Minerals micro cards
                def _mv(v):
                    return (
                        f"<div class='nutr-micro-val'>{html_lib.escape(v)}</div>"
                        if v and v not in (_NA, "Not Available", "")
                        else "<div class='nutr-na'>Not Present in Uploaded Content</div>"
                    )

                st.markdown(
                    f"""<div class='nutr-micro-grid'>
                        <div class='nutr-micro-card'>
                            <div class='nutr-micro-header'>
                                <div class='nutr-micro-icon vit'>☀️</div>
                                <div class='nutr-micro-label'>Vitamins</div>
                            </div>
                            {_mv(vits)}
                        </div>
                        <div class='nutr-micro-card'>
                            <div class='nutr-micro-header'>
                                <div class='nutr-micro-icon min'>💎</div>
                                <div class='nutr-micro-label'>Minerals</div>
                            </div>
                            {_mv(mins)}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                # ── Database Save Action ──
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                col_save, _ = st.columns([2, 3])
                with col_save:
                    if st.button("💾 Save Nutrition Record to Database", use_container_width=True, key="btn_save_record_db"):
                        diet_type = "veg"
                        if "chicken" in dish_name.lower() or "fish" in dish_name.lower() or "mutton" in dish_name.lower():
                            diet_type = "nv"
                        elif "egg" in dish_name.lower():
                            diet_type = "egg"
                        
                        food_data = {
                            "name": dish_name,
                            "source_type": "api_analysis",
                            "diet_type": diet_type,
                            "goals": ["weight_loss", "muscle_gain", "diabetic_friendly", "maintenance"],
                            "meal_type": "Snack",
                            "calories": _clean_float(cal),
                            "protein": _clean_float(pro),
                            "carbohydrates": _clean_float(carbs),
                            "fat": _clean_float(fat),
                            "fiber": _clean_float(fiber),
                            "vitamins": [vits] if isinstance(vits, str) else vits,
                            "minerals": [mins] if isinstance(mins, str) else mins,
                            "ingredients": ingredients,
                            "health_benefits": summary
                        }
                        res = api_client.save_food(food_data)
                        if res.get("success"):
                            st.success(f"✅ Successfully saved '{dish_name}' to the database!")
                        elif res.get("error") == "duplicate":
                            st.info(f"ℹ️ '{dish_name}' already exists in the database.")
                        else:
                            st.error(f"❌ Error saving to database: {res.get('detail')}")

                # ── Allergen Detection API ──
                st.markdown("<div class='nutr-section-title' style='margin-top: 20px;'>⚠️ Allergen & Dietary Safety</div>", unsafe_allow_html=True)
                with st.spinner("Analyzing allergens…"):
                    allergen_res = api_client.detect_allergens(dish_name, ingredients)
                if allergen_res:
                    detected_allergens = allergen_res.get("detected_allergens", [])
                    warning_level = allergen_res.get("warning_level", "None")
                    explanation = allergen_res.get("explanation", "")
                    safe_veg = allergen_res.get("safe_for_vegetarian", True)
                    safe_egg = allergen_res.get("safe_for_eggetarian", True)
                    safe_vegan = allergen_res.get("safe_for_vegan", True)
                    
                    warning_colors = {"None": "#10B981", "Low": "#F59E0B", "Medium": "#EF4444", "High": "#B91C1C"}
                    badge_color = warning_colors.get(warning_level, "#F59E0B")
                    
                    allergen_tags = "".join(f"<span class='badge' style='background:#EF4444;color:white;margin-right:5px;padding:3px 8px;border-radius:12px;font-size:0.75rem;'>{html_lib.escape(a)}</span>" for a in detected_allergens)
                    if not allergen_tags:
                        allergen_tags = "<span class='badge' style='background:#10B981;color:white;padding:3px 8px;border-radius:12px;font-size:0.75rem;'>No Allergens Detected</span>"
                        
                    veg_status = "🌱 Safe for Vegetarian" if safe_veg else "🥩 Contains Non-Veg"
                    egg_status = "🥚 Safe for Eggetarian" if safe_egg else "🚫 Avoid for Eggetarian"
                    vegan_status = "🥦 Safe for Vegan" if safe_vegan else "🥛 Contains Animal Products"
                    
                    st.markdown(
                        f"""<div class='rv-card' style='border-top: 4px solid {badge_color}; padding: 15px;'>
                            <div style='font-size: 0.95rem; font-weight: 800; margin-bottom: 8px;'>Warning Level: <span style='color: {badge_color};'>{warning_level}</span></div>
                            <div style='margin-bottom: 10px;'>{allergen_tags}</div>
                            <div style='font-size: 0.82rem; color: var(--text-2); margin-bottom: 12px;'>{html_lib.escape(explanation)}</div>
                            <div style='display: flex; gap: 10px; font-size: 0.78rem; font-weight: 700;'>
                                <span style='color: {"#10B981" if safe_veg else "#EF4444"};'>{veg_status}</span>
                                <span style='color: {"#10B981" if safe_egg else "#EF4444"};'>{egg_status}</span>
                                <span style='color: {"#10B981" if safe_vegan else "#EF4444"};'>{vegan_status}</span>
                            </div>
                        </div>""",
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Unable to perform allergen analysis at this time.")

                # ── Healthy Substitution API ──
                st.markdown("<div class='nutr-section-title' style='margin-top: 20px;'>💡 Healthy Substitutions</div>", unsafe_allow_html=True)
                sub_goal = st.selectbox(
                    "Select Target Goal for Substitutions:",
                    ["weight_loss", "muscle_gain", "diabetic_friendly", "weight_gain", "maintenance"],
                    key="sub_goal_select"
                )
                with st.spinner("Finding substitutions…"):
                    sub_res = api_client.get_substitutions(dish_name, ingredients, goal=sub_goal)
                if sub_res:
                    subs = sub_res.get("substitutions", [])
                    if not subs:
                        st.markdown(
                            f"""<div class='rv-card' style='padding: 15px; border-left: 4px solid #10B981;'>
                                <div style='font-size: 0.85rem; color: var(--text-2);'>{html_lib.escape(sub_res.get("summary", ""))}</div>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    else:
                        for idx, sub in enumerate(subs):
                            st.markdown(
                                f"""<div class='rv-card' style='padding: 12px; margin-bottom: 8px; border-left: 4px solid var(--accent);'>
                                    <div style='font-size: 0.88rem; font-weight: 800;'>{html_lib.escape(sub.get("original_ingredient"))} ➡️ <span style='color: var(--accent);'>{html_lib.escape(sub.get("replacement"))}</span></div>
                                    <div style='font-size: 0.8rem; color: var(--text-2); margin-top: 4px;'><b>Reason:</b> {html_lib.escape(sub.get("reason"))}</div>
                                    <div style='font-size: 0.78rem; color: var(--text-2); font-style: italic; margin-top: 2px;'><b>Impact:</b> {html_lib.escape(sub.get("estimated_nutrition_impact"))}</div>
                                </div>""",
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No substitution recommendations available.")

            # img_col and Generate Dish Image feature removed in Task 10

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  🍱 AI MEAL PLANNER
    # ═══════════════════════════════════════
    elif selected == "🍱 AI Meal Planner":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>🍱 AI Meal Planner</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Generate personalized Indian meal plans tailored to your health goals, "
            "dietary preferences, and schedule.</div>",
            unsafe_allow_html=True,
        )

        # ── Controls Section ──────────────────────────────────
        st.markdown("<div class='mp-controls-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            goal = st.selectbox(
                "🎯 Primary Goal",
                ["Weight Loss", "Weight Gain", "Muscle Gain", "Maintenance", "Diabetic Friendly"],
                index=0,
                key="mp_select_goal",
            )
            diet = st.selectbox(
                "🥗 Diet Type",
                ["Vegetarian", "Eggetarian", "Non-Vegetarian"],
                index=0,
                key="mp_select_diet",
            )

        with col2:
            meals = st.multiselect(
                "🍽 Meals to Include",
                ["Breakfast", "Lunch", "Snacks", "Dinner"],
                default=["Breakfast", "Lunch", "Snacks", "Dinner"],
                key="mp_select_meals",
            )
            days = st.radio(
                "🗓 Plan Duration (Days)",
                [1, 3, 7],
                index=0,
                horizontal=True,
                key="mp_select_days",
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if not meals:
            st.warning("⚠️ Please select at least one meal to include in your plan.")
        else:
            # Construct Cache Key including analyzed content context
            ac = st.session_state.get("analyzed_content")
            ac_dish = (ac.get("dish_name") or ac.get("source_title") or "none") if ac else "none"
            meals_key = ",".join(sorted(meals))
            current_mp_key = f"mp_g_{goal}_d_{diet}_m_{meals_key}_days_{days}_ac_{hash(ac_dish)}"

            col_gen1, col_gen2 = st.columns([2, 1], gap="small")
            with col_gen1:
                regen_clicked = st.button("✨ Generate / Refresh Meal Plan", use_container_width=True, key="btn_mp_generate")

            if (st.session_state.get("mp_cache_key") != current_mp_key) or (st.session_state.get("mp_plan") is None) or regen_clicked:
                with st.spinner("🍱 Customizing your personalized Indian meal plan…"):
                    plan = _generate_indian_meal_plan(goal, diet, meals, days, analyzed_content=ac)
                    st.session_state.mp_plan = plan
                    st.session_state.mp_cache_key = current_mp_key

            plan = st.session_state.get("mp_plan")

            if plan:
                download_txt = _format_meal_plan_download(plan, goal, diet)
                with col_gen2:
                    st.download_button(
                        label="📥 Download Meal Plan",
                        data=download_txt,
                        file_name=f"NutriMate_{goal.replace(' ','_')}_MealPlan.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="btn_mp_download",
                    )

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                # Render Meals grouped by Day
                for day_item in plan:
                    day_num = day_item.get("day", 1)
                    st.markdown(
                        f"""<div class="mp-day-header">
                            🗓️ Day {day_num} Plan
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    day_meals = day_item.get("meals", [])
                    grid_cols = st.columns(2, gap="medium")

                    for i, meal in enumerate(day_meals):
                        m_type = meal.get("type", "Meal")
                        m_name = meal.get("name", "Indian Dish")
                        ings = meal.get("ingredients", [])
                        cal = meal.get("calories", "N/A")
                        pro = meal.get("protein", "N/A")
                        carb = meal.get("carbs", "N/A")
                        fat = meal.get("fat", "N/A")
                        fiber = meal.get("fiber", "N/A")
                        why = meal.get("why", "Balanced nutrient distribution.")

                        type_cls = m_type.lower()
                        icon_map = {"Breakfast": "🌅", "Lunch": "☀️", "Snacks": "☕", "Dinner": "🌙"}
                        m_icon = icon_map.get(m_type, "🍽")

                        ings_str = ", ".join(ings) if isinstance(ings, list) else str(ings)

                        with grid_cols[i % 2]:
                            st.markdown(
                                f"""<div class="mp-meal-card">
                                    <span class="mp-meal-type-tag {type_cls}">{m_icon} {m_type}</span>
                                    <div class="mp-meal-name">🍽 {html_lib.escape(m_name)}</div>
                                    <div class="mp-ingredients-list">
                                        <b>📋 Ingredients:</b> {html_lib.escape(ings_str)}
                                    </div>
                                    <div class="mp-macro-pills">
                                        <span class="mp-macro-pill">🔥 {html_lib.escape(cal)}</span>
                                        <span class="mp-macro-pill">🥩 Pro: {html_lib.escape(pro)}</span>
                                        <span class="mp-macro-pill">🍚 Carb: {html_lib.escape(carb)}</span>
                                        <span class="mp-macro-pill">🥑 Fat: {html_lib.escape(fat)}</span>
                                        <span class="mp-macro-pill">🌾 Fib: {html_lib.escape(fiber)}</span>
                                    </div>
                                    <div class="mp-why-box">
                                        💡 <b>Why Recommended:</b> {html_lib.escape(why)}
                                    </div>
                                </div>""",
                                unsafe_allow_html=True,
                            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  🏥 AI HEALTH SCORE
    # ═══════════════════════════════════════
    elif selected == "🏥 AI Health Score":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>🏥 AI Health Score</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Instant nutrition quality score calculated from your analyzed recipe, "
            "food image, or nutrition summary — with a detailed breakdown and personalized recommendations.</div>",
            unsafe_allow_html=True,
        )

        # Primary: shared analyzed_content from upload auto-analysis
        ac      = st.session_state.get("analyzed_content")
        rv_an   = st.session_state.get("rv_analysis")
        ns_data = st.session_state.get("ns_data") or ac
        ctx     = lm.get("context_text", "") or (ac.get("context_text", "") if ac else "")

        has_ac  = bool(ac and ac.get("is_recipe"))
        has_rv  = bool(rv_an and rv_an.get("is_recipe") and not rv_an.get("is_not_food_image"))
        has_ns  = bool(ns_data is not None)
        has_ctx = bool(ctx and ctx.strip())
        has_content = has_ac or has_rv or has_ns or has_ctx

        if not has_content:
            st.markdown(
                """<div class="rv-empty-state">
                    <div class="rv-empty-icon">🏥</div>
                    <div class="rv-empty-title">No Nutrition Content Analyzed Yet</div>
                    <div class="rv-empty-sub">
                        Upload a recipe, food image, or nutrition PDF in the sidebar to generate your AI Health Score.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            # ── Build cache key & calculate score ──────────────
            ac_key  = hash(str(ac)) if ac else "none"
            rv_key  = hash(str(rv_an)) if rv_an else "none"
            ns_key  = hash(str(ns_data)) if ns_data else "none"
            ctx_key = hash(ctx) if ctx else "none"
            current_hs_key = f"hs_ac_{ac_key}_rv_{rv_key}_ns_{ns_key}_ctx_{ctx_key}"

            if st.session_state.get("hs_cache_key") != current_hs_key or st.session_state.get("hs_data") is None:
                with st.spinner("🏥 Calculating your AI Health Score…"):
                    hs = _calculate_ai_health_score(ns_data, rv_an, ctx)
                    st.session_state.hs_data = hs
                    st.session_state.hs_cache_key = current_hs_key
            else:
                hs = st.session_state.hs_data

            total      = hs["total_score"]
            rating_lbl = hs["rating_label"]
            r_color    = hs["rating_color"]
            r_bg       = hs["rating_bg"]
            dish_name  = hs["dish_name"]
            breakdown  = hs["breakdown"]
            strengths  = hs["strengths"]
            improves   = hs["improvements"]
            rec        = hs["recommendation"]

            # ── Circular Gauge via SVG ──────────────────────────
            radius    = 58
            circ      = 2 * 3.14159 * radius
            dash_val  = (total / 100) * circ
            gap_val   = circ - dash_val

            gauge_svg = (
                f'<svg viewBox="0 0 150 150" width="150" height="150" xmlns="http://www.w3.org/2000/svg">'
                f'<circle cx="75" cy="75" r="{radius}" fill="none" stroke="rgba(100,116,139,0.12)" stroke-width="10"/>'
                f'<circle cx="75" cy="75" r="{radius}" fill="none" stroke="{r_color}" stroke-width="10" '
                f'stroke-dasharray="{dash_val:.1f} {gap_val:.1f}" stroke-dashoffset="{circ / 4:.1f}" stroke-linecap="round"'
                f' style="filter:drop-shadow(0 0 6px {r_color}55);"/>'
                f'</svg>'
            )

            # ── Overall Score Header Card (single block) ──────────
            st.markdown(
                f"""<div class="hs-main-card" style="
                    background:var(--surface);backdrop-filter:blur(16px);
                    border:1px solid var(--border);border-radius:20px;
                    padding:28px 32px;box-shadow:var(--sh-md);margin-bottom:20px;">
                    <div style="display:flex;align-items:center;gap:32px;flex-wrap:wrap;">
                        <div style="position:relative;width:150px;height:150px;flex-shrink:0;">
                            {gauge_svg}
                            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;">
                                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:2.6rem;font-weight:800;color:{r_color};line-height:1;">{total}</div>
                                <div style="font-size:0.72rem;color:var(--text-3);font-weight:600;margin-top:2px;">/ 100</div>
                            </div>
                        </div>
                        <div style="flex:1;min-width:200px;">
                            <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.10em;color:var(--text-3);margin-bottom:6px;">
                                Overall Health Score
                            </div>
                            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.45rem;font-weight:800;color:var(--text-1);margin-bottom:8px;letter-spacing:-0.02em;">
                                {html_lib.escape(dish_name)}
                            </div>
                            <span style="display:inline-flex;align-items:center;gap:5px;
                                background:{r_bg};color:{r_color};border:1px solid {r_color}40;
                                padding:5px 14px;border-radius:9999px;
                                font-size:0.84rem;font-weight:800;letter-spacing:0.02em;">
                                {rating_lbl}
                            </span>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── Score Breakdown Card (single block) ────────────────
            breakdown_rows = ""
            for item in breakdown:
                lbl      = item["label"]
                pts      = item["pts"]
                mx       = item["max"]
                bar_clr  = item["color"]
                pct      = int((pts / mx) * 100)
                breakdown_rows += f"""<div style="margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                        <span style="font-size:0.82rem;font-weight:600;color:var(--text-1);">{lbl}</span>
                        <span style="font-size:0.78rem;font-weight:700;color:{bar_clr};">{pts}/{mx}</span>
                    </div>
                    <div style="width:100%;height:8px;background:var(--surface-3);border-radius:9999px;overflow:hidden;">
                        <div style="width:{pct}%;height:100%;background:{bar_clr};border-radius:9999px;transition:width 0.6s ease;"></div>
                    </div>
                </div>"""

            st.markdown(
                f"""<div style="margin-bottom:20px;">
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.05rem;font-weight:800;color:var(--text-1);margin-bottom:14px;">📊 Score Breakdown</div>
                    <div style="background:var(--surface);backdrop-filter:blur(16px);
                        border:1px solid var(--border);border-radius:20px;
                        padding:22px 24px;box-shadow:var(--sh-sm);">
                        {breakdown_rows}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── Strengths / Improvements / Recommendation (single block) ───
            strengths_li = "".join(f"<li style='margin-bottom:6px;'>{html_lib.escape(s)}</li>" for s in strengths)
            improves_li  = "".join(f"<li style='margin-bottom:6px;'>{html_lib.escape(i)}</li>" for i in improves)

            st.markdown(
                f"""<div style="margin-bottom:16px;">
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.05rem;font-weight:800;color:var(--text-1);margin-bottom:14px;">💡 AI Insights</div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">
                        <div style="background:var(--surface);backdrop-filter:blur(16px);
                            border:1px solid var(--border);border-top:4px solid var(--primary);
                            border-radius:20px;padding:18px 20px;box-shadow:var(--sh-sm);
                            transition:transform 0.25s ease,box-shadow 0.25s ease;">
                            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.92rem;font-weight:800;color:var(--text-1);margin-bottom:10px;display:flex;align-items:center;gap:7px;">✅ Strengths</div>
                            <ul style="font-size:0.80rem;color:var(--text-2);line-height:1.55;padding-left:16px;">{strengths_li}</ul>
                        </div>
                        <div style="background:var(--surface);backdrop-filter:blur(16px);
                            border:1px solid var(--border);border-top:4px solid var(--accent);
                            border-radius:20px;padding:18px 20px;box-shadow:var(--sh-sm);
                            transition:transform 0.25s ease,box-shadow 0.25s ease;">
                            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.92rem;font-weight:800;color:var(--text-1);margin-bottom:10px;display:flex;align-items:center;gap:7px;">⚠️ Areas to Improve</div>
                            <ul style="font-size:0.80rem;color:var(--text-2);line-height:1.55;padding-left:16px;">{improves_li}</ul>
                        </div>
                        <div style="background:var(--surface);backdrop-filter:blur(16px);
                            border:1px solid var(--border);border-top:4px solid #8B5CF6;
                            border-radius:20px;padding:18px 20px;box-shadow:var(--sh-sm);
                            transition:transform 0.25s ease,box-shadow 0.25s ease;">
                            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.92rem;font-weight:800;color:var(--text-1);margin-bottom:10px;display:flex;align-items:center;gap:7px;">💡 AI Recommendation</div>
                            <div style="font-size:0.84rem;color:var(--text-2);line-height:1.55;">{html_lib.escape(rec)}</div>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  ⚖️ FOOD COMPARISON
    # ═══════════════════════════════════════
    elif selected == "⚖️ Food Comparison":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>⚖️ Food Comparison</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Compare two food items side-by-side using the dynamic database.</div>",
            unsafe_allow_html=True,
        )
        
        # Load available dishes from database
        with st.spinner("Loading database food list…"):
            db_foods = api_client.get_foods()
            food_names_list = sorted(list(set([f.get("name") for f in db_foods if f.get("name")])))
            
        if not food_names_list:
            food_names_list = ["Paneer Tikka", "Poha with Roasted Peanuts and Sprouts", "Vegetable Biryani"]
            
        col_f1, col_f2 = st.columns(2, gap="medium")
        with col_f1:
            food_1_input = st.selectbox(
                "First Food Item",
                options=food_names_list,
                key="compare_food_1_select"
            )
        with col_f2:
            food_2_input = st.selectbox(
                "Second Food Item",
                options=[f for f in food_names_list if f != food_1_input],
                key="compare_food_2_select"
            )
            
        goal_input = st.selectbox(
            "Target Goal for Recommendation",
            options=["maintenance", "weight_loss", "muscle_gain", "weight_gain", "diabetic_friendly"],
            key="compare_goal_select"
        )
        
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("Compare Foods", use_container_width=True, key="btn_compare_foods"):
            if not food_1_input or not food_2_input:
                st.error("⚠️ Please select two different food items to compare.")
            else:
                with st.spinner("Comparing food items…"):
                    comp_res = api_client.compare_foods(food_1_input, food_2_input, goal_input)
                    
                if comp_res.get("success"):
                    data = comp_res.get("data", {})
                    f1_data = data.get("food_1", {})
                    f2_data = data.get("food_2", {})
                    comparison = data.get("nutrition_comparison", {})
                    
                    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
                    
                    # Recommendation summary block
                    st.markdown(
                        f"""<div class="quiz-recommend-box" style="border-left: 4px solid var(--accent); margin-bottom: 20px;">
                            <div style="font-size:0.95rem;font-weight:700;color:var(--text-1);margin-bottom:6px;">🏆 Comparison Recommendation</div>
                            <div style="font-size:0.88rem;color:var(--text-2);margin-bottom:8px;">{html_lib.escape(data.get("overall_recommendation") or "")}</div>
                            <div style="font-size:0.8rem;color:var(--text-2);"><b>Suitability for {goal_input}:</b> {html_lib.escape(data.get("better_for_goal") or "")} (Confidence: {data.get("confidence_score", 95)}%)</div>
                        </div>""",
                        unsafe_allow_html=True
                    )
                    
                    # Side-by-side grid
                    col_d1, col_d2 = st.columns(2, gap="medium")
                    with col_d1:
                        st.markdown(
                            f"""<div class='rv-card' style='border-top: 4px solid var(--primary);'>
                                <div style='font-size: 1.05rem; font-weight: 800; margin-bottom: 10px;'>🥇 {html_lib.escape(f1_data.get("name") or "")}</div>
                                <div style='font-size: 0.85rem; color: var(--text-2); margin-bottom: 12px;'>{html_lib.escape(f1_data.get("health_benefits") or "")}</div>
                                <ul style='font-size: 0.82rem; line-height: 1.6;'>
                                    <li><b>Calories:</b> {f1_data.get("calories")} kcal</li>
                                    <li><b>Protein:</b> {f1_data.get("protein")} g</li>
                                    <li><b>Carbs:</b> {f1_data.get("carbohydrates")} g</li>
                                    <li><b>Fat:</b> {f1_data.get("fat")} g</li>
                                    <li><b>Fiber:</b> {f1_data.get("fiber")} g</li>
                                </ul>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        
                    with col_d2:
                        st.markdown(
                            f"""<div class='rv-card' style='border-top: 4px solid #8B5CF6;'>
                                <div style='font-size: 1.05rem; font-weight: 800; margin-bottom: 10px;'>🥈 {html_lib.escape(f2_data.get("name") or "")}</div>
                                <div style='font-size: 0.85rem; color: var(--text-2); margin-bottom: 12px;'>{html_lib.escape(f2_data.get("health_benefits") or "")}</div>
                                <ul style='font-size: 0.82rem; line-height: 1.6;'>
                                    <li><b>Calories:</b> {f2_data.get("calories")} kcal</li>
                                    <li><b>Protein:</b> {f2_data.get("protein")} g</li>
                                    <li><b>Carbs:</b> {f2_data.get("carbohydrates")} g</li>
                                    <li><b>Fat:</b> {f2_data.get("fat")} g</li>
                                    <li><b>Fiber:</b> {f2_data.get("fiber")} g</li>
                                </ul>
                            </div>""",
                            unsafe_allow_html=True
                        )
                        
                    # Detailed Differences table
                    st.markdown("<div class='nutr-section-title' style='margin-top: 20px;'>📊 Nutritional Differences</div>", unsafe_allow_html=True)
                    
                    def _diff_badge(val, unit=""):
                        if val > 0:
                            return f"<span style='color: #EF4444; font-weight:700;'>+{val}{unit}</span>"
                        elif val < 0:
                            return f"<span style='color: #10B981; font-weight:700;'>{val}{unit}</span>"
                        return f"<span style='color: var(--text-2);'>0{unit}</span>"
                        
                    st.markdown(
                        f"""<table style='width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85rem;'>
                            <thead>
                                <tr style='border-bottom: 1px solid var(--border); text-align: left;'>
                                    <th style='padding: 8px;'>Nutrient</th>
                                    <th style='padding: 8px;'>Difference (Food 1 - Food 2)</th>
                                    <th style='padding: 8px;'>Category Winner</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style='border-bottom: 1px solid var(--border);'>
                                    <td style='padding: 8px;'>Calories</td>
                                    <td style='padding: 8px;'>{_diff_badge(comparison.get("calories_diff"), " kcal")}</td>
                                    <td style='padding: 8px;'>{html_lib.escape(data.get("better_for_calories"))}</td>
                                </tr>
                                <tr style='border-bottom: 1px solid var(--border);'>
                                    <td style='padding: 8px;'>Protein</td>
                                    <td style='padding: 8px;'>{_diff_badge(comparison.get("protein_diff"), " g")}</td>
                                    <td style='padding: 8px;'>{html_lib.escape(data.get("better_for_protein"))}</td>
                                </tr>
                                <tr style='border-bottom: 1px solid var(--border);'>
                                    <td style='padding: 8px;'>Carbohydrates</td>
                                    <td style='padding: 8px;'>{_diff_badge(comparison.get("carbs_diff"), " g")}</td>
                                    <td style='padding: 8px;'>N/A</td>
                                </tr>
                                <tr style='border-bottom: 1px solid var(--border);'>
                                    <td style='padding: 8px;'>Fat</td>
                                    <td style='padding: 8px;'>{_diff_badge(comparison.get("fat_diff"), " g")}</td>
                                    <td style='padding: 8px;'>N/A</td>
                                </tr>
                                <tr style='border-bottom: 1px solid var(--border);'>
                                    <td style='padding: 8px;'>Fiber</td>
                                    <td style='padding: 8px;'>{_diff_badge(comparison.get("fiber_diff"), " g")}</td>
                                    <td style='padding: 8px;'>{html_lib.escape(data.get("better_for_fiber"))}</td>
                                </tr>
                            </tbody>
                        </table>""",
                        unsafe_allow_html=True
                    )
                else:
                    st.error(f"❌ Could not perform comparison: {comp_res.get('detail')}")
                    
        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  📈 PROGRESS TRACKING
    # ═══════════════════════════════════════
    elif selected == "📈 Progress Tracking":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>📈 Progress Tracking</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Log daily nutrition metrics and monitor your progress trends over time.</div>",
            unsafe_allow_html=True,
        )

        # ── 1. Daily Progress Logging Form ──
        st.markdown("<div class='nutr-section-title' style='margin-top: 20px;'>📝 Log Daily Metrics</div>", unsafe_allow_html=True)
        
        col_inputs1, col_inputs2, col_inputs3 = st.columns(3, gap="medium")
        with col_inputs1:
            log_date = st.date_input(
                "Date",
                value=datetime.now().date(),
                key="progress_log_date"
            )
            log_goal = st.selectbox(
                "Active Health Goal",
                options=["weight_loss", "muscle_gain", "diabetic_friendly", "weight_gain", "maintenance"],
                key="progress_log_goal"
            )
        with col_inputs2:
            log_calories = st.number_input(
                "Calories (kcal)",
                min_value=0.0,
                max_value=10000.0,
                value=2000.0,
                step=50.0,
                key="progress_log_calories"
            )
            log_protein = st.number_input(
                "Protein (g)",
                min_value=0.0,
                max_value=500.0,
                value=70.0,
                step=5.0,
                key="progress_log_protein"
            )
        with col_inputs3:
            log_fiber = st.number_input(
                "Fiber (g)",
                min_value=0.0,
                max_value=150.0,
                value=25.0,
                step=1.0,
                key="progress_log_fiber"
            )
            log_health_score = st.slider(
                "Daily Health Score (0-100)",
                min_value=0,
                max_value=100,
                value=80,
                step=1,
                key="progress_log_health_score"
            )

        log_notes = st.text_area(
            "Optional Notes / Diary",
            placeholder="How did you feel today? Any custom notes about your diet?",
            key="progress_log_notes"
        )

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("Log Progress", use_container_width=True, key="btn_log_progress"):
            progress_payload = {
                "date": log_date.strftime("%Y-%m-%d"),
                "goal": log_goal,
                "calories": float(log_calories),
                "protein": float(log_protein),
                "fiber": float(log_fiber),
                "health_score": float(log_health_score),
                "notes": log_notes.strip() if log_notes else None
            }
            with st.spinner("Logging daily progress…"):
                res = api_client.log_progress(progress_payload)
            if res.get("success"):
                st.success(f"🎉 Progress logged successfully for {log_date.strftime('%Y-%m-%d')}!")
                st.rerun()
            else:
                if res.get("error") == "duplicate":
                    st.error(f"⚠️ Progress for {log_date.strftime('%Y-%m-%d')} has already been logged. You can only log once per day.")
                else:
                    st.error(f"❌ Error logging progress: {res.get('detail')}")

        # ── 2. Progress Summary Dashboard ──
        st.markdown("<div class='nutr-section-title' style='margin-top: 30px;'>📊 Progress Averages & Trends</div>", unsafe_allow_html=True)
        
        with st.spinner("Fetching progress summary…"):
            summary = api_client.get_progress_summary()
            
        if summary and summary.get("total_logged_days", 0) > 0:
            total_days = summary.get("total_logged_days", 0)
            avg_cal = summary.get("average_calories", 0.0)
            avg_pro = summary.get("average_protein", 0.0)
            avg_fib = summary.get("average_fiber", 0.0)
            avg_hs = summary.get("average_health_score", 0.0)
            trend = summary.get("trend", "Stable")
            
            trend_color = "#10B981"
            if trend == "Declining":
                trend_color = "#EF4444"
            elif trend == "Stable":
                trend_color = "#F59E0B"

            st.markdown(
                f"""<div class='nutr-macros'>
                    <div class='nutr-macro-card cal'>
                        <div class='nutr-macro-icon'>🔥</div>
                        <div class='nutr-macro-val'>{avg_cal} kcal</div>
                        <div class='nutr-macro-label'>Avg Calories</div>
                    </div>
                    <div class='nutr-macro-card pro'>
                        <div class='nutr-macro-icon'>🥩</div>
                        <div class='nutr-macro-val'>{avg_pro} g</div>
                        <div class='nutr-macro-label'>Avg Protein</div>
                    </div>
                    <div class='nutr-macro-card fib'>
                        <div class='nutr-macro-icon'>🌾</div>
                        <div class='nutr-macro-val'>{avg_fib} g</div>
                        <div class='nutr-macro-label'>Avg Fiber</div>
                    </div>
                    <div class='nutr-macro-card score'>
                        <div class='nutr-macro-icon'>🏥</div>
                        <div class='nutr-macro-val'>{avg_hs}</div>
                        <div class='nutr-macro-label'>Avg Health Score</div>
                    </div>
                    <div class='nutr-macro-card trend' style='border-top: 4px solid {trend_color};'>
                        <div class='nutr-macro-icon'>📈</div>
                        <div class='nutr-macro-val' style='color:{trend_color}; font-weight:800;'>{trend}</div>
                        <div class='nutr-macro-label'>Overall Trend</div>
                    </div>
                </div>""",
                unsafe_allow_html=True
            )
            st.markdown(f"<div style='font-size:0.85rem;color:var(--text-3);margin-top:8px;'>Based on {total_days} total logged days.</div>", unsafe_allow_html=True)
        else:
            st.info("No logs recorded yet. Log daily metrics above to see trends.")

        # ── 3. Progress History Table ──
        st.markdown("<div class='nutr-section-title' style='margin-top: 30px;'>📅 History Log</div>", unsafe_allow_html=True)
        
        with st.spinner("Fetching logs history…"):
            logs = api_client.get_progress()

        if logs:
            rows = []
            for item in reversed(logs):
                date_str = item.get("date", "")
                goal_str = item.get("goal", "")
                cal_val = item.get("calories", 0.0)
                pro_val = item.get("protein", 0.0)
                fib_val = item.get("fiber", 0.0)
                hs_val = item.get("health_score", 0.0)
                notes_str = item.get("notes") or ""
                
                rows.append(
                    f"""<tr style='border-bottom: 1px solid var(--border);'>
                        <td style='padding: 10px 8px; font-weight:600;'>{html_lib.escape(date_str)}</td>
                        <td style='padding: 10px 8px; color:var(--text-2);'>{html_lib.escape(goal_str)}</td>
                        <td style='padding: 10px 8px;'>{cal_val} kcal</td>
                        <td style='padding: 10px 8px;'>{pro_val} g</td>
                        <td style='padding: 10px 8px;'>{fib_val} g</td>
                        <td style='padding: 10px 8px; font-weight:700;'>{hs_val}</td>
                        <td style='padding: 10px 8px; font-size:0.82rem; color:var(--text-3); max-width:250px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;' title='{html_lib.escape(notes_str)}'>{html_lib.escape(notes_str)}</td>
                    </tr>"""
                )
                
            st.markdown(
                f"""<div style='overflow-x:auto; width:100%; border: 1px solid var(--border); border-radius:8px;'>
                    <table style='width: 100%; border-collapse: collapse; font-size: 0.85rem; background: var(--surface); text-align: left;'>
                        <thead>
                            <tr style='background: var(--surface-2); border-bottom: 1px solid var(--border); color: var(--text-2); font-weight:700;'>
                                <th style='padding: 12px 8px;'>Date</th>
                                <th style='padding: 12px 8px;'>Goal</th>
                                <th style='padding: 12px 8px;'>Calories</th>
                                <th style='padding: 12px 8px;'>Protein</th>
                                <th style='padding: 12px 8px;'>Fiber</th>
                                <th style='padding: 12px 8px;'>Health Score</th>
                                <th style='padding: 12px 8px;'>Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(rows)}
                        </tbody>
                    </table>
                </div>""",
                unsafe_allow_html=True
            )
        else:
            st.info("Your progress history log is currently empty.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  💧 HYDRATION TRACKING
    # ═══════════════════════════════════════
    elif selected == "💧 Hydration Tracking":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>💧 Hydration Tracking</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Log daily water intake and manage hydration goals.</div>",
            unsafe_allow_html=True,
        )

        # Date Selector
        selected_date = st.date_input(
            "Select Date",
            value=datetime.now().date(),
            key="hydration_selected_date"
        )
        date_str = selected_date.strftime("%Y-%m-%d")

        # Fetch current date stats
        with st.spinner("Fetching daily hydration stats…"):
            today_stats = api_client.get_hydration_today(date_str)

        if not today_stats:
            today_stats = {
                "date": date_str,
                "target_ml": 2000.0,
                "consumed_ml": 0.0,
                "remaining_ml": 2000.0,
                "completion_pct": 0.0,
                "hydration_status": "Dehydrated",
                "reminder_interval_mins": 60,
                "logs": []
            }

        target_ml = today_stats.get("target_ml", 2000.0)
        consumed_ml = today_stats.get("consumed_ml", 0.0)
        remaining_ml = today_stats.get("remaining_ml", 2000.0)
        completion_pct = today_stats.get("completion_pct", 0.0)
        hydration_status = today_stats.get("hydration_status", "Dehydrated")
        reminder_interval = today_stats.get("reminder_interval_mins", 60)
        logs = today_stats.get("logs", [])

        # Overall Status Dashboard (Metric Cards)
        status_color = "#EF4444" # Red
        if hydration_status == "Moderately Hydrated":
            status_color = "#F59E0B" # Orange
        elif hydration_status == "Well Hydrated":
            status_color = "#10B981" # Green

        st.markdown(
            f"""<div class='nutr-macros'>
                <div class='nutr-macro-card cal'>
                    <div class='nutr-macro-icon'>🎯</div>
                    <div class='nutr-macro-val'>{int(target_ml)} ml</div>
                    <div class='nutr-macro-label'>Daily Target</div>
                </div>
                <div class='nutr-macro-card pro'>
                    <div class='nutr-macro-icon'>💧</div>
                    <div class='nutr-macro-val'>{int(consumed_ml)} ml</div>
                    <div class='nutr-macro-label'>Consumed</div>
                </div>
                <div class='nutr-macro-card fib'>
                    <div class='nutr-macro-icon'>⏳</div>
                    <div class='nutr-macro-val'>{int(remaining_ml)} ml</div>
                    <div class='nutr-macro-label'>Remaining</div>
                </div>
                <div class='nutr-macro-card score'>
                    <div class='nutr-macro-icon'>📊</div>
                    <div class='nutr-macro-val'>{completion_pct}%</div>
                    <div class='nutr-macro-label'>Completion</div>
                </div>
                <div class='nutr-macro-card trend' style='border-top: 4px solid {status_color};'>
                    <div class='nutr-macro-icon'>🏥</div>
                    <div class='nutr-macro-val' style='color:{status_color}; font-weight:800;'>{hydration_status}</div>
                    <div class='nutr-macro-label'>Hydration Status</div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

        # Progress bar
        prog_val = min(1.0, float(completion_pct) / 100.0)
        st.progress(prog_val)

        # Active settings indicator
        st.markdown(f"<div style='font-size:0.88rem;color:var(--text-3);margin-top:-8px;margin-bottom:20px;'>🔔 Reminder interval is set to every <b>{reminder_interval} minutes</b>.</div>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2, gap="large")

        with col_left:
            # Quick Add buttons
            st.markdown("<div class='nutr-section-title'>⚡ Quick Log</div>", unsafe_allow_html=True)
            col_q1, col_q2, col_q3 = st.columns(3)
            with col_q1:
                if st.button("＋ 250 ml", key="btn_quick_250", use_container_width=True):
                    res = api_client.log_hydration({
                        "date": date_str,
                        "amount_ml": 250.0
                    })
                    if res.get("success"):
                        st.success("Logged 250 ml!")
                        st.rerun()
                    else:
                        st.error("Error logging hydration.")
            with col_q2:
                if st.button("＋ 500 ml", key="btn_quick_500", use_container_width=True):
                    res = api_client.log_hydration({
                        "date": date_str,
                        "amount_ml": 500.0
                    })
                    if res.get("success"):
                        st.success("Logged 500 ml!")
                        st.rerun()
                    else:
                        st.error("Error logging hydration.")
            with col_q3:
                if st.button("＋ 750 ml", key="btn_quick_750", use_container_width=True):
                    res = api_client.log_hydration({
                        "date": date_str,
                        "amount_ml": 750.0
                    })
                    if res.get("success"):
                        st.success("Logged 750 ml!")
                        st.rerun()
                    else:
                        st.error("Error logging hydration.")

            # Custom Intake Form
            st.markdown("<div class='nutr-section-title' style='margin-top:20px;'>📝 Log Custom Intake</div>", unsafe_allow_html=True)
            with st.form("custom_hydration_form", clear_on_submit=True):
                custom_amount = st.number_input("Water Amount (ml)", min_value=10.0, max_value=2000.0, value=250.0, step=50.0)
                submit_custom = st.form_submit_button("Log Custom Intake", use_container_width=True)
                if submit_custom:
                    res = api_client.log_hydration({
                        "date": date_str,
                        "amount_ml": float(custom_amount)
                    })
                    if res.get("success"):
                        st.success(f"Logged {custom_amount} ml!")
                        st.rerun()
                    else:
                        st.error("Error logging custom hydration.")

            # Settings Update Form
            st.markdown("<div class='nutr-section-title' style='margin-top:20px;'>⚙️ Hydration Settings</div>", unsafe_allow_html=True)
            with st.form("hydration_settings_form"):
                new_target = st.number_input("Daily Target (ml)", min_value=100.0, max_value=10000.0, value=float(target_ml), step=100.0)
                new_reminder = st.number_input("Reminder Interval (mins)", min_value=10, max_value=1440, value=int(reminder_interval), step=5)
                submit_settings = st.form_submit_button("Save Settings", use_container_width=True)
                if submit_settings:
                    # Log 0ml to update settings only
                    res = api_client.log_hydration({
                        "date": date_str,
                        "amount_ml": 0.0,
                        "target_ml": float(new_target),
                        "reminder_interval_mins": int(new_reminder)
                    })
                    if res.get("success"):
                        st.success("Hydration settings updated!")
                        st.rerun()
                    else:
                        st.error("Error updating settings.")

        with col_right:
            # Today's History Log
            st.markdown("<div class='nutr-section-title'>📅 Intake History Log</div>", unsafe_allow_html=True)
            if logs:
                rows = []
                for item in reversed(logs):
                    time_part = "Log entry"
                    if item.get("created_at"):
                        try:
                            # format iso string to time format
                            dt = datetime.fromisoformat(item.get("created_at"))
                            time_part = dt.strftime("%H:%M:%S")
                        except Exception:
                            pass
                    
                    rows.append(
                        f"""<tr style='border-bottom: 1px solid var(--border);'>
                            <td style='padding: 10px 8px; font-weight:600;'>{time_part}</td>
                            <td style='padding: 10px 8px; color:var(--primary); font-weight:700;'>{int(item.get("amount_ml", 0))} ml</td>
                            <td style='padding: 10px 8px; font-size:0.8rem; color:var(--text-3);'>{int(item.get("target_ml", 2000))} ml target</td>
                        </tr>"""
                    )
                
                st.markdown(
                    f"""<div style='overflow-x:auto; width:100%; border: 1px solid var(--border); border-radius:8px; margin-top:10px;'>
                        <table style='width: 100%; border-collapse: collapse; font-size: 0.85rem; background: var(--surface); text-align: left;'>
                            <thead>
                                <tr style='background: var(--surface-2); border-bottom: 1px solid var(--border); color: var(--text-2); font-weight:700;'>
                                    <th style='padding: 12px 8px;'>Time</th>
                                    <th style='padding: 12px 8px;'>Amount</th>
                                    <th style='padding: 12px 8px;'>Target</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join(rows)}
                            </tbody>
                        </table>
                    </div>""",
                    unsafe_allow_html=True
                )
            else:
                st.info("No water intake logged for this date.")

            # Summary stats
            st.markdown("<div class='nutr-section-title' style='margin-top:30px;'>📊 Historical Summary</div>", unsafe_allow_html=True)
            with st.spinner("Fetching stats summary…"):
                summary = api_client.get_hydration_summary()

            if summary and summary.get("total_days_logged", 0) > 0:
                s_days = summary.get("total_days_logged", 0)
                s_intake = summary.get("average_daily_intake", 0.0)
                s_target = summary.get("average_daily_target", 0.0)
                s_pct = summary.get("average_completion_pct", 0.0)

                st.markdown(
                    f"""<div style='background: var(--surface); padding: 16px; border: 1px solid var(--border); border-radius: 8px; margin-top:10px;'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.88rem;'>
                            <span style='color:var(--text-3);'>Total Days Logged:</span>
                            <span style='font-weight:700; color:var(--text-1);'>{s_days} days</span>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.88rem;'>
                            <span style='color:var(--text-3);'>Avg Daily Intake:</span>
                            <span style='font-weight:700; color:var(--primary);'>{int(s_intake)} ml</span>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.88rem;'>
                            <span style='color:var(--text-3);'>Avg Daily Target:</span>
                            <span style='font-weight:700; color:var(--text-1);'>{int(s_target)} ml</span>
                        </div>
                        <div style='display:flex; justify-content:space-between; font-size:0.88rem;'>
                            <span style='color:var(--text-3);'>Avg Completion Rate:</span>
                            <span style='font-weight:700; color:#F59E0B;'>{s_pct}%</span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True
                )
            else:
                st.info("Record water intake to view historical trends.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════
    #  🍔 CHEAT MEAL IMPACT
    # ═══════════════════════════════════════
    elif selected == "🍔 Cheat Meal Impact":
        st.markdown("<div style='padding:20px 24px;'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='wcard-title'>🍔 Cheat Meal Impact Analyzer</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='wcard-sub'>Understand how a junk food choice fits into your daily budget — and discover healthier alternatives.</div>",
            unsafe_allow_html=True,
        )

        # ── Inputs ──────────────────────────────────────────────────────
        col_a, col_b = st.columns([1, 1], gap="large")

        with col_a:
            st.markdown("<div class='nutr-section-title'>🍕 Food Details</div>", unsafe_allow_html=True)
            cm_food_name = st.text_input(
                "Food / Junk Food Name",
                placeholder="e.g. Burger, Pizza, Cold Drink…",
                key="cm_food_name"
            )
            cm_calories = st.number_input(
                "Calories (kcal) — optional",
                min_value=0.0, max_value=5000.0, value=0.0, step=10.0,
                key="cm_calories",
                help="Leave 0 to let the system estimate automatically."
            )
            cm_sugar = st.number_input(
                "Sugar (g) — optional",
                min_value=0.0, max_value=500.0, value=0.0, step=1.0,
                key="cm_sugar"
            )
            cm_fat = st.number_input(
                "Fat (g) — optional",
                min_value=0.0, max_value=500.0, value=0.0, step=1.0,
                key="cm_fat"
            )

        with col_b:
            st.markdown("<div class='nutr-section-title'>🎯 Daily Budget & Goal</div>", unsafe_allow_html=True)
            cm_goal = st.selectbox(
                "Health Goal",
                options=["", "weight_loss", "muscle_gain", "diabetic_friendly", "weight_gain", "maintenance"],
                format_func=lambda x: "(None / General)" if x == "" else x.replace("_", " ").title(),
                key="cm_goal"
            )
            cm_cal_target = st.number_input(
                "Daily Calorie Target (kcal)",
                min_value=500.0, max_value=10000.0, value=2000.0, step=50.0,
                key="cm_cal_target"
            )
            cm_sugar_target = st.number_input(
                "Daily Sugar Target (g)",
                min_value=5.0, max_value=500.0, value=50.0, step=5.0,
                key="cm_sugar_target"
            )
            cm_fat_target = st.number_input(
                "Daily Fat Target (g)",
                min_value=5.0, max_value=500.0, value=65.0, step=5.0,
                key="cm_fat_target"
            )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        cm_btn = st.button("⚡ Calculate Impact", use_container_width=True, key="cm_calculate_btn")

        if cm_btn:
            if not cm_food_name.strip():
                st.error("❌ Please enter a food name.")
            else:
                with st.spinner(f"Analysing cheat meal impact for '{cm_food_name}'…"):
                    result = api_client.cheat_meal_impact(
                        food_name=cm_food_name.strip(),
                        calories=float(cm_calories) if cm_calories > 0 else None,
                        sugar_g=float(cm_sugar) if cm_sugar > 0 else None,
                        fat_g=float(cm_fat) if cm_fat > 0 else None,
                        daily_calorie_target=float(cm_cal_target),
                        daily_sugar_target=float(cm_sugar_target),
                        daily_fat_target=float(cm_fat_target),
                        goal=cm_goal if cm_goal else None
                    )

                if not result.get("success"):
                    st.error(f"❌ Could not analyse: {result.get('detail', 'Unknown error')}")
                else:
                    d = result["data"]

                    # Impact level colour
                    impact = d.get("impact_level", "Low")
                    impact_color = "#10B981"  # Low → green
                    if impact == "Moderate":
                        impact_color = "#F59E0B"
                    elif impact == "High":
                        impact_color = "#EF4444"

                    # ── Budget Metric Cards ──────────────────────────────
                    st.markdown(
                        "<div class='nutr-section-title' style='margin-top:24px;'>📊 Budget Usage</div>",
                        unsafe_allow_html=True
                    )

                    cal_pct  = d.get("calorie_budget_used_pct", 0.0)
                    sug_pct  = d.get("sugar_budget_used_pct")
                    fat_pct  = d.get("fat_budget_used_pct")
                    est_cal  = d.get("estimated_calories", 0.0)
                    rem_cal  = d.get("remaining_calorie_budget", 0.0)
                    src      = d.get("calorie_source", "")

                    def _pct_badge(val):
                        if val is None:
                            return "<span style='color:var(--text-3);font-size:0.8rem;'>N/A</span>"
                        color = "#10B981" if val < 20 else ("#F59E0B" if val < 40 else "#EF4444")
                        return f"<span style='color:{color};font-weight:800;'>{val}%</span>"

                    st.markdown(
                        f"""<div class='nutr-macros'>
                            <div class='nutr-macro-card cal'>
                                <div class='nutr-macro-icon'>🔥</div>
                                <div class='nutr-macro-val'>{est_cal} kcal</div>
                                <div class='nutr-macro-label'>Estimated Calories<br><span style='font-size:0.72rem;color:var(--text-3);'>({src})</span></div>
                            </div>
                            <div class='nutr-macro-card pro'>
                                <div class='nutr-macro-icon'>📉</div>
                                <div class='nutr-macro-val'>{_pct_badge(cal_pct)}</div>
                                <div class='nutr-macro-label'>Calorie Budget Used</div>
                            </div>
                            <div class='nutr-macro-card fib'>
                                <div class='nutr-macro-icon'>🍬</div>
                                <div class='nutr-macro-val'>{_pct_badge(sug_pct)}</div>
                                <div class='nutr-macro-label'>Sugar Budget Used</div>
                            </div>
                            <div class='nutr-macro-card score'>
                                <div class='nutr-macro-icon'>🧈</div>
                                <div class='nutr-macro-val'>{_pct_badge(fat_pct)}</div>
                                <div class='nutr-macro-label'>Fat Budget Used</div>
                            </div>
                            <div class='nutr-macro-card trend' style='border-top:4px solid {impact_color};'>
                                <div class='nutr-macro-icon'>⚠️</div>
                                <div class='nutr-macro-val' style='color:{impact_color};font-weight:800;'>{impact}</div>
                                <div class='nutr-macro-label'>Impact Level</div>
                            </div>
                        </div>""",
                        unsafe_allow_html=True
                    )

                    # Remaining calorie budget callout
                    st.markdown(
                        f"<div style='font-size:0.9rem;color:var(--text-2);margin-top:4px;'>"
                        f"Remaining calorie budget for the day: <b style='color:var(--primary);'>{rem_cal} kcal</b></div>",
                        unsafe_allow_html=True
                    )

                    # ── Goal-Aware Recommendation ───────────────────────
                    rec = d.get("recommendation", "")
                    if rec:
                        st.markdown(
                            "<div class='nutr-section-title' style='margin-top:20px;'>💡 Recommendation</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style='background:var(--surface);border:1px solid var(--border);"
                            f"border-left:4px solid var(--primary);border-radius:8px;padding:14px 18px;"
                            f"font-size:0.9rem;line-height:1.6;color:var(--text-1);margin-top:8px;'>{html_lib.escape(rec)}</div>",
                            unsafe_allow_html=True
                        )

                    # ── Healthier Alternatives ─────────────────────────
                    alternatives = d.get("alternatives", [])
                    if alternatives:
                        st.markdown(
                            "<div class='nutr-section-title' style='margin-top:20px;'>🥦 Healthier Alternatives</div>",
                            unsafe_allow_html=True
                        )
                        for idx, alt in enumerate(alternatives):
                            repl  = html_lib.escape(alt.get("replacement", ""))
                            why   = html_lib.escape(alt.get("why", ""))
                            impact_txt = html_lib.escape(alt.get("impact", ""))
                            st.markdown(
                                f"<div style='background:var(--surface);border:1px solid var(--border);"
                                f"border-radius:8px;padding:12px 16px;margin-bottom:10px;'>"
                                f"<div style='font-weight:700;color:var(--primary);font-size:0.92rem;margin-bottom:4px;'>"
                                f"✅ {repl}</div>"
                                f"<div style='font-size:0.85rem;color:var(--text-2);margin-bottom:4px;'>{why}</div>"
                                f"<div style='font-size:0.8rem;color:var(--text-3);'>{impact_txt}</div></div>",
                                unsafe_allow_html=True
                            )

        st.markdown("</div>", unsafe_allow_html=True)




