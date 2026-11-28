# -*- coding: utf-8 -*-
"""Generate production-ready styles.css with full-screen vegetable background image and sidebar image."""
import base64
import os

main_img_path = "c:/nutrimate/assets/user_bg.jpg"
with open(main_img_path, "rb") as f:
    b64_main_img = base64.b64encode(f.read()).decode("utf-8")

sb_img_path = "c:/nutrimate/assets/sidebar_bg.jpg"
with open(sb_img_path, "rb") as f:
    b64_sb_img = base64.b64encode(f.read()).decode("utf-8")

sb_url = "https://media.istockphoto.com/id/1390699669/photo/assortment-of-healthy-food-for-clean-eating-flexitarian-mediterranean-diet.jpg?s=612x612&w=0&k=20&c=riJ9OUUAPS2KEDgQh7dOpsbaoDGeRPkq1x4RRVtTucE="

css_content = f"""@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ═══════════════════════════════════════════════════════════════
   NUTRIMATE — FIXED DARK GLASS THEME SYSTEM
   Vegetable Background × Glassmorphism × Emerald Green Accents
   ═══════════════════════════════════════════════════════════════ */

:root {{
  /* Backgrounds & Glass Surfaces */
  --bg:           transparent;
  --surface:      rgba(14, 22, 17, 0.72);
  --surface-solid:rgba(18, 28, 22, 0.85);
  --surface-2:    rgba(22, 34, 27, 0.78);
  --surface-3:    rgba(28, 44, 35, 0.82);
  --card:         rgba(16, 26, 20, 0.75);

  /* Brand & Accents */
  --primary:        #10B981;
  --primary-hover:  #059669;
  --primary-glow:   rgba(16, 185, 129, 0.38);
  --primary-soft:   rgba(16, 185, 129, 0.18);
  --secondary:      #34D399;
  --secondary-soft: rgba(52, 211, 153, 0.15);
  --accent:         #F59E0B;
  --accent-soft:    rgba(245, 158, 11, 0.15);

  /* High-Contrast White Typography */
  --text-1:    #FFFFFF;
  --text-2:    #F1F5F9;
  --text-3:    #CBD5E1;
  --text-inv:  #0F172A;

  /* Borders & Dividers */
  --border:    rgba(255, 255, 255, 0.16);
  --border-2:  rgba(255, 255, 255, 0.28);

  /* Sidebar Tokens */
  --sb-bg:         rgba(6, 12, 9, 0.88);
  --sb-surface:    rgba(16, 26, 20, 0.82);
  --sb-border:     rgba(255, 255, 255, 0.12);
  --sb-text:       #E2E8F0;
  --sb-text-hi:    #FFFFFF;
  --sb-active-bg:  rgba(16, 185, 129, 0.25);
  --sb-active-text:#10B981;

  /* Shadows */
  --sh-sm: 0 4px 20px rgba(0, 0, 0, 0.45);
  --sh-md: 0 8px 32px rgba(0, 0, 0, 0.60);
  --sh-lg: 0 16px 48px rgba(0, 0, 0, 0.75);

  /* Radii */
  --r-sm:   8px;
  --r-md:   12px;
  --r-lg:   16px;
  --r-xl:   20px;
  --r-2xl:  24px;
  --r-full: 9999px;

  --t-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --t-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --t-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
}}

/* ═══════════════════════════════════════════════════════════════
   RESET & TRANSPARENT STREAMLIT CONTAINERS FOR VISIBLE BACKGROUND
   ═══════════════════════════════════════════════════════════════ */
*, *::before, *::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

/* Force all Streamlit root wrapper elements to be TRANSPARENT so background shows through */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
.main, .block-container {{
  background: transparent !important;
  color: var(--text-1) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  -webkit-font-smoothing: antialiased;
}}

/* 1. Full-Screen Vegetable Background Image Layer */
.stApp::before {{
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100vw; height: 100vh;
  background-image: url('data:image/jpeg;base64,{b64_main_img}') !important;
  background-size: cover !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  background-attachment: fixed !important;
  z-index: -9999 !important;
}}

/* 2. Dark Semi-Transparent Overlay for Perfect Contrast & Readability */
.stApp::after {{
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100vw; height: 100vh;
  background: linear-gradient(135deg, rgba(6, 12, 9, 0.75) 0%, rgba(10, 18, 13, 0.82) 100%) !important;
  z-index: -9998 !important;
  pointer-events: none !important;
}}

/* Hide Default Streamlit Chrome Header & Footer */
header[data-testid="stHeader"], footer, #MainMenu {{
  background: transparent !important;
}}

/* ═══════════════════════════════════════════════════════════════
   GLOBAL TYPOGRAPHY & HEADINGS (ALL WHITE / HIGH CONTRAST)
   ═══════════════════════════════════════════════════════════════ */
h1, h2, h3, h4, h5, h6,
.wcard-title, .page-title, .section-heading, .rv-empty-title,
.mp-day-label, .hs-score-num, .hs-insight-title, .ns-card-title,
.quiz-q, .nutr-section-title {{
  color: #FFFFFF !important;
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  font-weight: 700;
  letter-spacing: -0.02em;
}}

p, span, li, label, div,
.wcard-sub, .page-sub, .rv-empty-sub, .ns-card-body,
.hs-score-denom, .stMarkdown p, .stMarkdown span, .stMarkdown li {{
  color: #F1F5F9 !important;
}}

.section-label {{
  color: #CBD5E1 !important;
}}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR STYLING WITH CUSTOM BACKGROUND IMAGE & DARK OVERLAY
   ═══════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {{
  background-image: linear-gradient(rgba(6, 12, 9, 0.82), rgba(8, 14, 10, 0.90)), url('data:image/jpeg;base64,{b64_sb_img}') !important;
  background-size: cover !important;
  background-position: center !important;
  background-repeat: no-repeat !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  border-right: 1px solid var(--sb-border) !important;
}}

section[data-testid="stSidebar"] * {{
  color: #FFFFFF !important;
}}

.sb-logo {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 12px 12px;
  border-bottom: 1px solid var(--sb-border);
  margin-bottom: 12px;
}}

.sb-logo-icon {{
  font-size: 1.8rem;
  background: var(--primary-soft);
  border: 1px solid var(--primary-glow);
  border-radius: var(--r-md);
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}}

.sb-logo-text {{
  display: flex;
  flex-direction: column;
}}

.sb-logo-name {{
  font-size: 1.15rem;
  font-weight: 800;
  color: #FFFFFF !important;
  letter-spacing: -0.02em;
}}

.sb-logo-sub {{
  font-size: 0.72rem;
  color: #10B981 !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.sb-divider {{
  height: 1px;
  background: var(--sb-border);
  margin: 12px 0;
}}

.sb-section {{
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #10B981 !important;
  margin: 14px 8px 8px;
}}

/* Sidebar Radio Navigation */
.stRadio > div[role="radiogroup"] {{
  gap: 4px !important;
}}

.stRadio > div[role="radiogroup"] > label {{
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: var(--r-md) !important;
  padding: 8px 12px !important;
  margin: 0 !important;
  transition: all var(--t-fast) !important;
  cursor: pointer !important;
}}

.stRadio > div[role="radiogroup"] > label:hover {{
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
}}

.stRadio > div[role="radiogroup"] > label:has(input:checked) {{
  background: var(--sb-active-bg) !important;
  border: 1px solid var(--primary-glow) !important;
  box-shadow: 0 0 12px var(--primary-glow) !important;
}}

.stRadio > div[role="radiogroup"] > label:has(input:checked) p,
.stRadio > div[role="radiogroup"] > label:has(input:checked) span {{
  color: #10B981 !important;
  font-weight: 700 !important;
}}

.stRadio > div[role="radiogroup"] > label p,
.stRadio > div[role="radiogroup"] > label span {{
  font-size: 0.88rem !important;
  color: #F1F5F9 !important;
}}

/* Knowledge Base Status Card */
.kb-card {{
  background: rgba(20, 30, 24, 0.85);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: var(--r-md);
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}}

.kb-card.empty {{
  border-color: rgba(245, 158, 11, 0.3);
}}

.kb-dot {{ font-size: 1rem; }}
.kb-text {{ font-size: 0.82rem; font-weight: 700; color: #FFFFFF !important; }}
.kb-sub {{ font-size: 0.72rem; color: #CBD5E1 !important; }}
.sb-file {{ font-size: 0.78rem; color: #F1F5F9 !important; padding: 4px 8px; background: rgba(255, 255, 255, 0.06); border-radius: var(--r-sm); margin-bottom: 4px; }}

/* ═══════════════════════════════════════════════════════════════
   GLASSMORPHISM CARDS & CONTAINERS
   ═══════════════════════════════════════════════════════════════ */
.wcard, .panel, .rv-card, .ns-card, .quiz-recommend-box,
.nutr-macro-card, .mp-meal-card, .hs-insight-card,
div[data-testid="stExpander"] {{
  background: var(--surface) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: var(--sh-md) !important;
  color: #FFFFFF !important;
}}

.wcard-title {{
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 4px;
  color: #FFFFFF !important;
}}

.wcard-sub {{
  font-size: 0.9rem;
  color: #CBD5E1 !important;
  margin-bottom: 20px;
}}

.nutr-section-title {{
  font-size: 1.1rem;
  font-weight: 700;
  color: #FFFFFF !important;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS (EMERALD GREEN PRIMARY & SOFT GLASS SECONDARY)
   ═══════════════════════════════════════════════════════════════ */
.stButton > button {{
  background: rgba(255, 255, 255, 0.08) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  font-weight: 600 !important;
  padding: 10px 18px !important;
  transition: all var(--t-fast) !important;
}}

.stButton > button:hover {{
  background: rgba(255, 255, 255, 0.16) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
  color: #FFFFFF !important;
  transform: translateY(-1px);
}}

/* Primary Action Buttons */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {{
  background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 4px 16px var(--primary-glow) !important;
  font-weight: 700 !important;
}}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {{
  background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
}}

/* ═══════════════════════════════════════════════════════════════
   FORM CONTROLS (INPUTS, DROPDOWNS, SELECTBOXES, TEXTAREAS)
   ═══════════════════════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > textarea {{
  background: rgba(10, 16, 12, 0.85) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--border-2) !important;
  border-radius: var(--r-md) !important;
  padding: 10px 14px !important;
  font-size: 0.92rem !important;
}}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > textarea:focus {{
  border-color: #10B981 !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
}}

.stSelectbox > div > div,
.stMultiSelect > div > div {{
  background: rgba(10, 16, 12, 0.85) !important;
  border: 1px solid var(--border-2) !important;
  border-radius: var(--r-md) !important;
}}

.stSelectbox > div > div *,
.stMultiSelect > div > div * {{
  color: #FFFFFF !important;
}}

div[data-baseweb="select"] ul {{
  background: rgba(14, 22, 17, 0.95) !important;
  border: 1px solid var(--border) !important;
}}

div[data-baseweb="select"] li {{
  color: #FFFFFF !important;
}}

div[data-baseweb="select"] li:hover {{
  background: var(--primary-soft) !important;
}}

/* ═══════════════════════════════════════════════════════════════
   TABLES & DATA GRIDS (FOOD COMPARISON, PROGRESS, HYDRATION)
   ═══════════════════════════════════════════════════════════════ */
table {{
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  background: rgba(14, 22, 17, 0.70) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  overflow: hidden !important;
  margin-top: 10px !important;
}}

th {{
  background: rgba(16, 185, 129, 0.18) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  padding: 12px 16px !important;
  border-bottom: 1px solid var(--border) !important;
  text-align: left !important;
}}

td {{
  padding: 10px 16px !important;
  color: #F1F5F9 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}}

tr:last-child td {{
  border-bottom: none !important;
}}

tr:hover td {{
  background: rgba(255, 255, 255, 0.05) !important;
}}

/* Streamlit Dataframe Overrides */
div[data-testid="stDataFrame"] {{
  background: rgba(14, 22, 17, 0.70) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
}}

/* ═══════════════════════════════════════════════════════════════
   CHAT UI & MESSAGES
   ═══════════════════════════════════════════════════════════════ */
.stChatMessage {{
  background: rgba(18, 28, 22, 0.75) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  margin-bottom: 12px !important;
}}

.stChatInput {{
  background: rgba(10, 16, 12, 0.90) !important;
  border: 1px solid var(--border-2) !important;
  border-radius: var(--r-xl) !important;
}}

.stChatInput textarea {{
  color: #FFFFFF !important;
}}

.user-block {{ max-width: 75%; float: right; margin-bottom: 12px; }}
.user-bubble {{
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: #FFFFFF !important;
  padding: 12px 18px;
  border-radius: 18px 18px 2px 18px;
  font-size: 0.92rem;
  box-shadow: 0 4px 16px var(--primary-glow);
}}

.ai-av {{
  width: 32px; height: 32px;
  border-radius: var(--r-full);
  background: var(--primary-soft);
  border: 1px solid var(--primary-glow);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
}}

.ai-name {{ font-size: 0.85rem; font-weight: 700; color: #FFFFFF !important; }}

/* ═══════════════════════════════════════════════════════════════
   NUTRITION MACRO CARDS & METRICS
   ═══════════════════════════════════════════════════════════════ */
.nutr-macros {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  margin-top: 14px;
}}

.nutr-macro-card {{
  background: rgba(18, 28, 23, 0.80) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  padding: 16px;
  text-align: center;
  transition: transform var(--t-fast);
}}

.nutr-macro-card:hover {{
  transform: translateY(-2px);
  border-color: var(--primary-glow) !important;
}}

.nutr-macro-card.cal   {{ border-top: 4px solid #EF4444 !important; }}
.nutr-macro-card.pro   {{ border-top: 4px solid #3B82F6 !important; }}
.nutr-macro-card.fib   {{ border-top: 4px solid #10B981 !important; }}
.nutr-macro-card.score {{ border-top: 4px solid #F59E0B !important; }}
.nutr-macro-card.trend {{ border-top: 4px solid #8B5CF6 !important; }}

.nutr-macro-icon {{ font-size: 1.4rem; margin-bottom: 4px; }}
.nutr-macro-val  {{ font-size: 1.35rem; font-weight: 800; color: #FFFFFF !important; }}
.nutr-macro-label{{ font-size: 0.78rem; color: #CBD5E1 !important; font-weight: 600; margin-top: 2px; }}

/* ═══════════════════════════════════════════════════════════════
   FLIP CARDS (NUTRITION CARDS WORKSPACE)
   ═══════════════════════════════════════════════════════════════ */
.nc-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}}

@media (max-width: 1100px) {{ .nc-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 680px)  {{ .nc-grid {{ grid-template-columns: 1fr; }} }}

.nc-flip-wrap {{ perspective: 1000px; height: 320px; width: 100%; }}
.nc-flip-inner {{
  position: relative; width: 100%; height: 100%; text-align: left;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}}

.nc-flip-wrap:hover .nc-flip-inner {{ transform: rotateY(180deg); }}

.nc-flip-front, .nc-flip-back {{
  position: absolute; width: 100%; height: 100%;
  backface-visibility: hidden; -webkit-backface-visibility: hidden;
  border-radius: var(--r-xl); padding: 20px;
  background: rgba(18, 28, 23, 0.88) !important;
  backdrop-filter: blur(14px) !important;
  border: 1px solid var(--border) !important;
  display: flex; flex-direction: column; justify-content: space-between;
}}

.nc-front-hero {{
  background: rgba(16, 185, 129, 0.15) !important;
  border: 1px solid rgba(16, 185, 129, 0.3) !important;
  border-radius: var(--r-md);
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}}

.nc-front-title {{
  color: #FFFFFF !important;
  font-size: 1.1rem;
  font-weight: 800;
}}

.nc-flip-back {{ transform: rotateY(180deg); }}

.nc-back-title {{
  font-size: 1.05rem;
  font-weight: 800;
  color: #10B981 !important;
}}

/* ═══════════════════════════════════════════════════════════════
   MEAL PLANNER WORKSPACE
   ═══════════════════════════════════════════════════════════════ */
.mp-day-header {{
  display: flex; align-items: center; gap: 12px; margin: 24px 0 12px;
}}

.mp-day-label {{ font-size: 1.15rem; font-weight: 800; color: #FFFFFF !important; }}
.mp-day-divider {{ flex: 1; height: 1px; background: rgba(16, 185, 129, 0.3); }}

.mp-meal-card {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  padding: 16px; margin-bottom: 12px;
}}

.mp-macro-pill {{
  font-size: 0.74rem; font-weight: 700; color: #FFFFFF !important;
  padding: 3px 8px; border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.1); border: 1px solid var(--border);
}}

/* ═══════════════════════════════════════════════════════════════
   HEALTH SCORE WORKSPACE
   ═══════════════════════════════════════════════════════════════ */
.hs-gauge-wrap {{ display: flex; justify-content: center; margin: 16px 0 10px; }}
.hs-score-num {{ font-size: 2.8rem; font-weight: 800; color: #FFFFFF !important; }}
.hs-score-denom{{ font-size: 0.75rem; color: #CBD5E1 !important; font-weight: 600; }}

.hs-insights-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
@media (max-width: 900px) {{ .hs-insights-grid {{ grid-template-columns: 1fr; }} }}

.hs-insight-card.strengths      {{ border-top: 4px solid #10B981 !important; }}
.hs-insight-card.improvements   {{ border-top: 4px solid #F59E0B !important; }}
.hs-insight-card.recommendation {{ border-top: 4px solid #8B5CF6 !important; }}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE DESIGN & DESKTOP OPTIMIZATIONS
   ═══════════════════════════════════════════════════════════════ */
.main .block-container {{
  max-width: 1280px !important;
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}}

@media (max-width: 768px) {{
  .main .block-container {{
    padding-left: 1rem !important;
    padding-right: 1rem !important;
  }}
}}
"""

with open("c:/nutrimate/styles.css", "w", encoding="utf-8") as f:
    f.write(css_content)

print(f"Written updated styles.css (Length: {len(css_content)} bytes)")
