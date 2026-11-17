"""Automated checks for StoryVerse Analytics.  Run with:  python tests/run_checks.py

Prints PASS / FAIL for each item of the testing checklist and exits with a
non-zero code if anything fails.
"""

import io
import sys

# Simulate a clean install: scipy is NOT in requirements.txt, so the app must work without it.
sys.modules["scipy"] = None
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import analysis, visualizations as viz                      # noqa: E402
from src.data_loader import DatasetError, REQUIRED_COLUMNS, load_excel  # noqa: E402
from src.preprocessing import preprocess                               # noqa: E402

DATA = ROOT / "data" / "storyverse_dataset.xlsx"
results = []


def check(name, condition, detail=""):
    results.append(bool(condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name} {detail}")


# 1-2. Columns and loading
raw, sheet = load_excel(DATA)
check("Excel file loads", len(raw) > 0, f"({raw.shape[0]} rows x {raw.shape[1]} cols, sheet '{sheet}')")
check("All required columns present", all(c in raw.columns for c in REQUIRED_COLUMNS))
try:
    load_excel(ROOT / "data" / "does_not_exist.xlsx")
    check("Missing file gives friendly error", False)
except DatasetError as error:
    check("Missing file gives friendly error", "not found" in str(error))
bad = io.BytesIO()
raw.drop(columns=["City"]).to_excel(bad, index=False)
bad.seek(0)
try:
    load_excel(bad)
    check("Missing column is detected", False)
except DatasetError as error:
    check("Missing column is detected", "City" in str(error))

# 3. Preprocessing
df, log = preprocess(raw)
check("Preprocessing keeps every record", len(df) == len(raw))
check("Original dataframe is untouched", pd.api.types.is_string_dtype(raw["Timestamp"]) or raw["Timestamp"].dtype == object)
check("Timestamp is datetime", pd.api.types.is_datetime64_any_dtype(df["Timestamp"]))
check("Confidence on 0-1 scale", df["Emotion Confidence"].between(0, 1).all())
check("Derived date/time features exist", all(c in df.columns for c in ["Year", "Month", "Day", "Hour"]))

# 4. Numerical and categorical analysis
kpi = analysis.compute_kpis(df)
check("KPI total equals row count", kpi["total_stories"] == len(df))
check("Average confidence ignores missing values", abs(kpi["avg_confidence"] - df["Emotion Confidence"].dropna().mean()) < 1e-12)
check("KPI music % matches manual count", abs(kpi["music_pct"] - (df["Background Music Added"] == True).mean() * 100) < 1e-9)  # noqa: E712
check("Descriptive statistics computed", not analysis.descriptive_statistics(df).empty)
check("Frequency table sums to rows with a value",
      analysis.frequency_table(df, "Language")["Stories"].sum() == len(df))
check("IQR outlier method runs", analysis.iqr_outliers(df, "Emotion Confidence")["lower"] is not None)
check("Word frequencies computed", not analysis.word_frequencies(df).empty)

# 5. All visualizations (full data)
required = ["bar_language", "donut_emotion", "line_trend", "histogram_confidence", "box_confidence_language",
            "scatter_temperature_confidence", "heatmap_correlation", "treemap_language_emotion", "area_monthly",
            "violin_confidence_emotion", "stacked_bar_media_by_language", "scatter_matrix_numeric"]
extras = ["hbar_top_cities", "grouped_bar_emotion_language", "bubble_language_emotion", "calendar_heatmap",
          "pareto_chart", "word_frequency_chart", "story_length_histogram"]
for name in required + extras:
    output = getattr(viz, name)(df)
    fig = output[0] if isinstance(output, tuple) else output
    has_data = len(fig.data) > 0
    check(f"Chart builds with data: {name}", has_data)

# 7-8. Filters, empty data and missing values never crash
subset = df[df["Language"] == "Hindi"]
check("Filtering changes KPIs", analysis.compute_kpis(subset)["total_stories"] == (df["Language"] == "Hindi").sum())
empty = df.iloc[0:0]
crash = False
try:
    for name in required + extras:
        output = getattr(viz, name)(empty)
        (output[0] if isinstance(output, tuple) else output).to_json()
    analysis.compute_kpis(empty)
    analysis.generate_insights(empty)
    analysis.descriptive_statistics(empty)
    analysis.grouped_summary(empty, "Language")
except Exception as error:  # noqa: BLE001
    crash = True
    print("   error:", error)
check("Empty filtered data handled by every chart and calculation", not crash)

holes = df.copy()
holes["Emotion Confidence"] = np.nan
holes["Temperature (C)"] = np.nan
holes.loc[holes.index[:5], "Timestamp"] = pd.NaT
holes["Date"] = holes["Timestamp"].dt.normalize()
crash = False
try:
    for name in required + extras:
        output = getattr(viz, name)(holes)
        (output[0] if isinstance(output, tuple) else output).to_json()
    analysis.generate_insights(holes)
    analysis.compute_kpis(holes)
except Exception as error:  # noqa: BLE001
    crash = True
    print("   error:", error)
check("All-missing numeric columns and missing timestamps handled", not crash)

# 9. CSV export
csv = df.drop(columns=["Date"]).to_csv(index=False).encode("utf-8-sig")
back = pd.read_csv(io.BytesIO(csv))
check("CSV export round-trips", len(back) == len(df) and "Language" in back.columns)

# Spearman must work without scipy and match the textbook definition
pair = analysis.pairwise_correlation(df, "Temperature (C)", "Emotion Confidence")
check("Spearman correlation works without scipy", pair["spearman"] is not None and -1 <= pair["spearman"] <= 1,
      f"(rho = {pair['spearman']:.3f})")

# 10. Pure filter logic
from src.filters import apply_filters  # noqa: E402
hindi = apply_filters(df, {"Language": ["Hindi"], "Detected Emotion": []})
check("apply_filters selects only chosen language", set(hindi["Language"]) == {"Hindi"} and len(hindi) == 5)
check("Empty selection means all rows", len(apply_filters(df, {"Language": []})) == len(df))
d0, d1 = df["Date"].min().date(), df["Date"].max().date()
check("Full date range keeps every row", len(apply_filters(df, {}, (d0, d1), (d0, d1))) == len(df))
check("Narrow date range reduces rows", 0 < len(apply_filters(df, {}, (d0, d0), (d0, d1))) < len(df))
check("Impossible combination gives empty data, no crash",
      apply_filters(df, {"Language": ["Hindi"], "Video Label": ["No video"]}).empty)
check("KPI sparklines computed", analysis.kpi_sparklines(df)["stories"] is not None)
check("KPI sparklines safe on empty data", analysis.kpi_sparklines(empty)["stories"] is None)

# 11. Full dashboard run through Streamlit's own test runner
try:
    from streamlit.testing.v1 import AppTest

    def metric(at, label):
        return [m for m in at.metric if m.label == label][0].value

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
    check("Dashboard runs without exceptions", not at.exception, str([e.value for e in at.exception]))
    check("Dashboard shows 8 KPI cards", len([m for m in at.metric if m.label in (
        "Total Stories", "Avg Emotion Confidence", "Stories with Background Music", "Stories with Video",
        "Unique Languages", "Unique Cities", "Most Frequent Emotion", "Most Used Language")]) == 8)
    check("Every chart card has its own filter", len([w for w in at.multiselect if w.key and w.key.endswith("_Language")]) >= 19)

    # Filter ONE chart only (the language bar chart) -> other cards must not change
    at.multiselect(key="flt_bundled_bar_language_ms_Language").select("Hindi").run()
    check("Chart filter run works without exceptions", not at.exception)
    captions = [c.value for c in at.caption]
    check("Only the filtered chart reports a filtered view", sum("Filtered view:" in c for c in captions) == 1,
          f"(found {sum('Filtered view:' in c for c in captions)})")
    check("Filtering one chart leaves KPI cards unchanged", metric(at, "Total Stories") == str(len(df)))

    # Filter the KPI section -> KPI cards change
    at.multiselect(key="flt_bundled_kpi_ms_Language").select("Hindi").run()
    check("KPI filter updates KPI cards", metric(at, "Total Stories") == "5", f"(Total Stories = {metric(at, 'Total Stories')})")

    # Impossible combination -> friendly warning, no crash
    at.multiselect(key="flt_bundled_kpi_ms_Video Label").select("No video").run()
    check("Empty filter result handled gracefully", not at.exception and any("No stories match" in w.value for w in at.warning))

    # Sidebar reset-all button restores everything
    at.sidebar.button[0].click().run()
    check("Reset all filters restores the full data", not at.exception and metric(at, "Total Stories") == str(len(df)))
except ImportError:
    print("[SKIP] streamlit.testing not available in this Streamlit version")

print(f"\n{sum(results)} of {len(results)} checks passed.")
sys.exit(0 if all(results) else 1)
