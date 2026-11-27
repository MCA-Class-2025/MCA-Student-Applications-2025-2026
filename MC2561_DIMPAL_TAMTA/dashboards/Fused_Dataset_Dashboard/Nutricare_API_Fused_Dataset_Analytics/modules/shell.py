"""Shared page shell: header, theme, top navigation, horizontal filter bar. Every page calls `ctx = shell.setup()` first,
so filter values (session_state keys) survive page changes. There is no sidebar."""
from types import SimpleNamespace
import streamlit as st
from . import ui
from .data import SUPPORT, counts, filter_df, load_data, to_csv_bytes
from .theme import DEFAULT_THEME, THEMES

Z = "​"
NAV = [("app.py", "1 · Main Dashboard"), ("pages/1_Nutrition_Analysis.py", "2 · Nutrition"),
       ("pages/2_Food_Quality_Processing.py", "3 · Food Quality"), ("pages/3_Cancer_Classification.py", "4 · Cancer Classification"),
       ("pages/4_Production_Geographic.py", "5 · Production & Maps"), ("pages/5_Statistics_Data_Explorer.py", "6 · Statistics & Data")]
KEYS = ["f_food", "f_hindi", "f_marathi", "f_nutri", "f_nova", "f_risk", "f_support", "f_country", "f_state"]


def _ver():
    try: return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception: return (1, 40)


def stretch():
    return {"width": "stretch"} if _ver() >= (1, 50) else {"use_container_width": True}


def clear_filters():
    for k in KEYS: st.session_state[k] = []


def card(key, title, sub=""):
    c = st.container(key=f"card_{key}")
    c.markdown(ui.title(title, sub), unsafe_allow_html=True)
    return c


def plot(fig, key):
    st.plotly_chart(fig, key=f"pc_{key}", config={"displaylogo": False, "displayModeBar": "hover"}, **stretch())


def food_picker(d, key, label="Select food"):
    """Dropdown that remembers the chosen food across pages; returns that food's row."""
    names = sorted(d["Food Name"]); cur = st.session_state.get("food_sel")
    idx = names.index(cur) if cur in names else (names.index("Cornstarch") if "Cornstarch" in names else 0)
    f = st.selectbox(label, names, index=idx, key=key)
    st.session_state["food_sel"] = f
    return d[d["Food Name"] == f].iloc[0]


def setup(main=False):
    st.set_page_config(page_title="API Fused Dataset Analytics", page_icon="🥗", layout="wide", initial_sidebar_state="collapsed")
    for k in KEYS: st.session_state.setdefault(k, [])
    df, q = load_data()
    T = THEMES[st.session_state.get("theme_name", DEFAULT_THEME)]
    st.markdown(ui.css(T), unsafe_allow_html=True)

    hb, h1, h2, h3 = st.columns([8, 1.2, 1.2, 1.0], vertical_alignment="center")
    hb.markdown(ui.banner(f"{q['rows']:,} foods · {q['cols'] - 2} columns"), unsafe_allow_html=True)
    with h1.popover("Theme", **stretch()):
        st.radio("Theme", list(THEMES), key="theme_name")
        st.markdown(ui.swatches(THEMES), unsafe_allow_html=True)
    with h2.popover("Info", **stretch()):
        st.markdown(
            f"**Data quality** (nothing hidden)\n\n- {q['rows']:,} foods · {q['cols'] - 2} source columns\n"
            f"- {q['missing_cells']} missing nutrient cells in {q['rows_missing']} rows (kept blank, never 0)\n"
            f"- {q['dup_rows']} fully duplicated rows · {q['dup_names']} repeated food names\n"
            f"- {q['unknown_country']} foods with 'Unknown' top country · {q['not_in_india']} 'Not produced in India'\n"
            f"- {q['no_score']} foods have no Nutri-Score ('-')\n- {q['assumptions']} rows carry an Assumption note (proxy crop)\n\n"
            "Cancer text has ~1,400 distinct values; where grouped, the prefix before ' - ' is used (Risk factor / Protective / Neutral / Limit or avoid). "
            "These are dataset classifications, not medical advice.")
    dl = h3.container()

    for c, (path, label) in zip(st.columns(len(NAV)), NAV):
        c.page_link(path, label=label, **stretch())

    s = st.session_state
    with st.expander("🔎 Filters (horizontal · apply to every page)", expanded=main):
        with st.form("filters", border=False):
            r1 = st.columns(5)
            r1[0].multiselect("Food Name", sorted(df["Food Name"]), key="f_food")
            r1[1].multiselect("Hindi Name", sorted(df["Hindi Name"].dropna().unique()), key="f_hindi")
            r1[2].multiselect("Marathi Name", sorted(df["Marathi Name"].dropna().unique()), key="f_marathi")
            r1[3].multiselect("Nutri-Score Grade", ["A", "B", "C", "D", "E", "-"], key="f_nutri")
            r1[4].multiselect("NOVA Group", sorted(df["NOVA Group"].unique()), key="f_nova")
            r2 = st.columns([1.3, 1.3, 1.2, 1.2, .7, .7], vertical_alignment="bottom")
            r2[0].multiselect("Cancer Risk Classification", sorted(df["Risk Group"].unique()), key="f_risk")
            r2[1].multiselect("Cancer Patient Support Category", sorted(df[SUPPORT].unique()), key="f_support")
            r2[2].multiselect("Producing Country", sorted(counts(df["Top 3 Producing Countries"])), key="f_country")
            r2[3].multiselect("Producing Indian State", sorted(counts(df["Top 3 Producing Indian States"])), key="f_state")
            r2[4].form_submit_button("Apply Filters", type="primary", **stretch())
            r2[5].form_submit_button("Clear Filters", on_click=clear_filters, **stretch())
    d = filter_df(df, s["f_nutri"], s["f_nova"], s["f_risk"], s["f_support"], s["f_country"], s["f_state"],
                  foods=s["f_food"], hindi=s["f_hindi"], marathi=s["f_marathi"])
    dl.download_button(Z, data=to_csv_bytes(d), file_name="fused_dataset_filtered.csv", mime="text/csv",
                       icon=":material/download:", help="Download filtered rows (CSV)", **stretch())
    active = sum(bool(s[k]) for k in KEYS)
    st.markdown(f"<div class='hint'><b>{len(d):,}</b> of {len(df):,} foods match · {active} filter(s) active</div>", unsafe_allow_html=True)
    if d.empty:
        st.warning("No foods match the current filters. Press Clear Filters.")
        st.stop()
    return SimpleNamespace(df=df, d=d, q=q, T=T, dark=T["mode"] == "dark")
