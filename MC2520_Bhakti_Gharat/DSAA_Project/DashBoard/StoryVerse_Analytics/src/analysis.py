"""Statistical calculations, grouped summaries, correlations and automatic insights.

Every number shown in the dashboard is calculated here from the (filtered) data.
Nothing is hardcoded.
"""

import string
from collections import Counter
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.preprocessing import NOT_RECORDED, find_inconsistent_labels

NUMERIC_ANALYSIS_COLUMNS = ["Emotion Confidence", "Temperature (C)", "Story Word Count"]

# Columns that are identifiers, free text or file paths: not meaningful for statistics.
NON_STATISTICAL_COLUMNS = {
    "Story ID": "Unique identifier (every value is different)",
    "Title": "Free text, unique per story",
    "Source / Prompt": "Free text prompt",
    "Story Text": "Free text (used only for text analysis: length and word frequency)",
    "Audio File Path": "File path (only tells whether audio exists)",
    "Video File Path": "File path (only tells whether a video exists)",
}

# Small built-in stop-word lists (no internet or NLTK download needed).
ENGLISH_STOP_WORDS = set("""
a about above after again all also am an and any are as at be because been before being below between both but by
can could did do does doing down during each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just let me more most my myself no nor not now of off on once only or
other our ours ourselves out over own same she should so some such than that the their theirs them themselves then
there these they this those through to too under until up very was we were what when where which while who whom why
will with would you your yours yourself yourselves one two s t d ll m o re ve y said say says like little
""".split())

# A few very common Hindi / Marathi function words.
INDIC_STOP_WORDS = set("""
का की के को में से है हैं था थी थे और भी तो पर एक यह वह ने कि जो इस उस था हो गया गई गए रहा रही लिए
आणि या ते हे ही हा च त्या त्यात होते होती होता आहे आहेत एक की मध्ये ला ने ना पण तर
""".split())

STOP_WORDS = ENGLISH_STOP_WORDS | INDIC_STOP_WORDS
PUNCTUATION = string.punctuation + "।॥“”‘’—–…"


# --------------------------------------------------------------------------- #
# A. Data understanding (works on the RAW dataframe)
# --------------------------------------------------------------------------- #
def dtype_table(df: pd.DataFrame) -> pd.DataFrame:
    """Column name, data type, non-null count and unique count."""
    return pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(t) for t in df.dtypes],
        "Non-Null": df.notna().sum().values,
        "Unique Values": [df[c].nunique(dropna=True) for c in df.columns],
    })


def missing_value_table(df: pd.DataFrame) -> pd.DataFrame:
    """Missing values per column with an explanation of whether they are expected."""
    expected_media = {"Audio File Path": "Expected: path is empty when audio was not created",
                      "Video File Path": "Expected: path is empty when no video was created"}
    rows = []
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        if n_missing == 0:
            note = "Complete"
        elif col in expected_media:
            note = expected_media[col]
        elif col in ("City", "Weather Condition", "Temperature (C)") and "Mode" in df.columns:
            # Check the actual relationship instead of assuming it.
            weather_rows = df["Mode"].astype(str).str.contains("weather", case=False, na=False)
            only_weather = bool(df.loc[~weather_rows, col].isna().all()) and not df.loc[weather_rows, col].isna().any()
            note = ("Expected: recorded only for Weather-Based stories" if only_weather
                    else "Check: missing values do not follow the story Mode")
        else:
            note = "Needs attention"
        rows.append({"Column": col, "Missing": n_missing,
                     "Missing %": round(100 * n_missing / len(df), 1) if len(df) else 0.0, "Note": note})
    return pd.DataFrame(rows)


def categorical_unique_values(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Unique values (with counts) of the categorical columns."""
    rows = []
    for col in columns:
        counts = df[col].value_counts(dropna=False)
        rows.append({"Column": col, "Unique": int(df[col].nunique(dropna=True)),
                     "Values (count)": ", ".join(f"{k} ({v})" for k, v in counts.items())})
    return pd.DataFrame(rows)


def timestamp_summary(raw_ts: pd.Series) -> Dict[str, object]:
    """Convert raw timestamps and describe the date range."""
    ts = pd.to_datetime(raw_ts, errors="coerce")
    valid = ts.dropna()
    if valid.empty:
        return {"valid": 0, "invalid": int(len(ts))}
    return {
        "valid": int(len(valid)), "invalid": int(ts.isna().sum()),
        "start": valid.min(), "end": valid.max(),
        "span_days": int((valid.max() - valid.min()).days),
        "distinct_days": int(valid.dt.normalize().nunique()),
        "distinct_months": int(valid.dt.to_period("M").nunique()),
    }


def data_quality_summary(raw: pd.DataFrame, processed: pd.DataFrame) -> Dict[str, object]:
    """One dictionary with the headline data-quality numbers."""
    total_cells = raw.shape[0] * raw.shape[1]
    missing_cells = int(raw.isna().sum().sum())
    unexpected = missing_value_table(raw)
    unexpected = unexpected[~unexpected["Note"].str.startswith(("Complete", "Expected"))]
    return {
        "rows": raw.shape[0], "columns": raw.shape[1],
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_story_ids": int(raw["Story ID"].duplicated().sum()),
        "missing_cells": missing_cells,
        "missing_pct": round(100 * missing_cells / total_cells, 1) if total_cells else 0.0,
        "columns_with_unexpected_missing": unexpected["Column"].tolist(),
        "inconsistent_labels": find_inconsistent_labels(raw),
        "invalid_timestamps": int(pd.to_datetime(raw["Timestamp"], errors="coerce").isna().sum()),
        "confidence_scale": processed.attrs.get("confidence_scale", "unknown"),
        "rows_after_cleaning": processed.shape[0],
    }


# --------------------------------------------------------------------------- #
# D. KPIs
# --------------------------------------------------------------------------- #
def _top_value(series: pd.Series) -> Tuple[str, int]:
    """Most frequent non-missing, non-'Not recorded' value and its count."""
    counts = series[series != NOT_RECORDED].dropna().value_counts()
    if counts.empty:
        return "N/A", 0
    return str(counts.index[0]), int(counts.iloc[0])


def compute_kpis(df: pd.DataFrame) -> Dict[str, object]:
    """Calculate all KPI values from the (filtered) dataframe."""
    n = len(df)
    conf = df["Emotion Confidence"].dropna()          # missing values are ignored, not zero
    top_emotion, top_emotion_n = _top_value(df["Detected Emotion"])
    top_language, top_language_n = _top_value(df["Language"])
    music_known = df["Background Music Added"].dropna()
    video_known = df["Video Created"].dropna()
    return {
        "total_stories": n,
        "unique_languages": int(df.loc[df["Language"] != NOT_RECORDED, "Language"].nunique()),
        "unique_cities": int(df.loc[df["City"] != NOT_RECORDED, "City"].nunique()),
        "avg_confidence": float(conf.mean()) if len(conf) else None,
        "music_pct": float(music_known.astype(bool).mean() * 100) if len(music_known) else None,
        "video_pct": float(video_known.astype(bool).mean() * 100) if len(video_known) else None,
        "top_emotion": top_emotion, "top_emotion_count": top_emotion_n,
        "top_language": top_language, "top_language_count": top_language_n,
        "confidence_valid_n": int(len(conf)),
    }


# --------------------------------------------------------------------------- #
# F. Statistical analysis
# --------------------------------------------------------------------------- #
def frequency_table(df: pd.DataFrame, column: str, include_not_recorded: bool = False) -> pd.DataFrame:
    """Counts and percentages of a categorical column."""
    series = df[column].dropna()
    if not include_not_recorded:
        series = series[series != NOT_RECORDED]
    counts = series.value_counts()
    total = counts.sum()
    out = counts.rename_axis(column).reset_index(name="Stories")
    out["Percent"] = (out["Stories"] / total * 100).round(1) if total else 0.0
    return out


def descriptive_statistics(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Count, mean, median, std, min, quartiles and max for numeric columns."""
    columns = columns or NUMERIC_ANALYSIS_COLUMNS
    rows = []
    for col in columns:
        s = df[col].dropna()
        if s.empty:
            continue
        rows.append({
            "Variable": col, "Valid N": int(s.count()), "Mean": s.mean(), "Median": s.median(),
            "Std Dev": s.std() if len(s) > 1 else np.nan, "Min": s.min(),
            "Q1 (25%)": s.quantile(0.25), "Q3 (75%)": s.quantile(0.75), "Max": s.max(),
        })
    return pd.DataFrame(rows).round(3)


def correlation_matrix(df: pd.DataFrame, columns: Optional[List[str]] = None,
                       min_pairs: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pearson correlation (pairwise complete) and the number of pairs behind each cell.

    Cells with fewer than `min_pairs` valid pairs are set to NaN because a
    correlation from a handful of points is not reliable.
    """
    columns = columns or NUMERIC_ANALYSIS_COLUMNS
    columns = [c for c in columns if c in df.columns and df[c].nunique(dropna=True) > 1]
    if len(columns) < 2:
        return pd.DataFrame(), pd.DataFrame()
    data = df[columns]
    corr = data.corr(method="pearson", min_periods=min_pairs)
    valid = data.notna().astype(int)
    pair_counts = valid.T.dot(valid)
    return corr, pair_counts


def pairwise_correlation(df: pd.DataFrame, col_a: str, col_b: str) -> Dict[str, object]:
    """Pearson and Spearman correlation between two columns using complete pairs only."""
    pair = df[[col_a, col_b]].dropna()
    result: Dict[str, object] = {"n": int(len(pair)), "pearson": None, "spearman": None}
    if len(pair) >= 3 and pair[col_a].nunique() > 1 and pair[col_b].nunique() > 1:
        result["pearson"] = float(pair[col_a].corr(pair[col_b], method="pearson"))
        # Spearman = Pearson correlation of the ranks (done by hand so SciPy is not required).
        result["spearman"] = float(pair[col_a].rank().corr(pair[col_b].rank(), method="pearson"))
    return result


def describe_correlation(r: float) -> str:
    """Plain-English strength label for a correlation coefficient."""
    a = abs(r)
    strength = ("very weak" if a < 0.2 else "weak" if a < 0.4 else "moderate" if a < 0.6
                else "strong" if a < 0.8 else "very strong")
    return f"{strength} {'positive' if r > 0 else 'negative'}"


def grouped_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Story count, average confidence, music % and video % per group."""
    if df.empty:
        return pd.DataFrame()
    grouped = df.groupby(group_col, dropna=False)
    out = pd.DataFrame({
        "Stories": grouped.size(),
        "Avg Confidence": grouped["Emotion Confidence"].mean(),
        "Median Confidence": grouped["Emotion Confidence"].median(),
        "Avg Word Count": grouped["Story Word Count"].mean(),
        "Music %": grouped["Background Music Added"].apply(lambda s: s.dropna().astype(bool).mean() * 100 if s.notna().any() else np.nan),
        "Video %": grouped["Video Created"].apply(lambda s: s.dropna().astype(bool).mean() * 100 if s.notna().any() else np.nan),
    }).reset_index()
    return out.sort_values("Stories", ascending=False).round(3)


def iqr_outliers(df: pd.DataFrame, column: str) -> Dict[str, object]:
    """Detect potential outliers with the 1.5 x IQR rule."""
    s = df[column].dropna()
    if len(s) < 4:
        return {"n": int(len(s)), "q1": None, "q3": None, "lower": None, "upper": None, "outliers": pd.DataFrame()}
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (df[column] < lower) | (df[column] > upper)
    cols = [c for c in ["Story ID", "Title", "Language", "Detected Emotion", column] if c in df.columns]
    return {"n": int(len(s)), "q1": float(q1), "q3": float(q3), "iqr": float(iqr),
            "lower": float(lower), "upper": float(upper), "outliers": df.loc[mask, cols]}


def multimedia_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Share of stories that have audio, background music and video."""
    items = {"Audio file present": df["Has Audio File"], "Background music added": df["Background Music Added"],
             "Video created": df["Video Created"]}
    rows = []
    for name, series in items.items():
        known = series.dropna()
        yes = int(known.astype(bool).sum())
        rows.append({"Media type": name, "Stories with it": yes, "Stories without": int(len(known) - yes),
                     "Percent": round(yes / len(known) * 100, 1) if len(known) else np.nan})
    return pd.DataFrame(rows)


# ---- text analysis -------------------------------------------------------- #
def tokenize(text: str) -> List[str]:
    """Split on spaces and strip punctuation (keeps Devanagari words intact)."""
    words = [w.strip(PUNCTUATION).lower() for w in str(text).split()]
    return [w for w in words if len(w) > 2 and not w.isdigit()]


def word_frequencies(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Most common words in Story Text after removing stop words."""
    counter: Counter = Counter()
    for text in df["Story Text"].dropna():
        counter.update(w for w in tokenize(text) if w not in STOP_WORDS)
    return pd.DataFrame(counter.most_common(top_n), columns=["Word", "Count"])


# ---- time series ---------------------------------------------------------- #
def daily_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Stories per calendar day, including days with zero stories."""
    dates = df["Date"].dropna()
    if dates.empty:
        return pd.DataFrame(columns=["Date", "Stories"])
    counts = dates.value_counts().sort_index()
    full = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    out = counts.reindex(full, fill_value=0).rename_axis("Date").reset_index(name="Stories")
    return out


def monthly_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Stories per calendar month, including months with zero stories."""
    dates = df["Date"].dropna()
    if dates.empty:
        return pd.DataFrame(columns=["Month", "Stories"])
    periods = dates.dt.to_period("M").value_counts().sort_index()
    full = pd.period_range(periods.index.min(), periods.index.max(), freq="M")
    out = periods.reindex(full, fill_value=0)
    return pd.DataFrame({"Month": [str(p) for p in out.index], "Stories": out.values})


def pareto_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Counts sorted high-to-low with the cumulative percentage (for a Pareto chart)."""
    freq = frequency_table(df, column)
    if freq.empty:
        return freq
    freq["Cumulative %"] = (freq["Stories"].cumsum() / freq["Stories"].sum() * 100).round(1)
    return freq


# --------------------------------------------------------------------------- #
# H. Automatic insights
# --------------------------------------------------------------------------- #
def generate_insights(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """Return a list of (level, message) insights computed from the filtered data.

    level is 'info' or 'warning'.
    """
    insights: List[Tuple[str, str]] = []
    n = len(df)
    if n == 0:
        return [("warning", "No stories match the current filters, so no insights can be calculated.")]

    kpis = compute_kpis(df)

    # Language & emotion frequency
    if kpis["top_language"] != "N/A":
        share = kpis["top_language_count"] / n * 100
        insights.append(("info", f"**{kpis['top_language']}** is the most used language: "
                                 f"{kpis['top_language_count']} of {n} stories ({share:.1f}%)."))
    if kpis["top_emotion"] != "N/A":
        share = kpis["top_emotion_count"] / n * 100
        insights.append(("info", f"**{kpis['top_emotion']}** is the most frequently detected emotion "
                                 f"({kpis['top_emotion_count']} stories, {share:.1f}%)."))

    # Confidence
    conf = df["Emotion Confidence"].dropna()
    if len(conf) >= 2:
        insights.append(("info", f"Average emotion confidence is **{conf.mean():.3f}** (median {conf.median():.3f}, "
                                 f"range {conf.min():.3f}–{conf.max():.3f}). Values are well below 1, so the detector "
                                 "is not highly certain about most stories."))
        by_emotion = df.groupby("Detected Emotion")["Emotion Confidence"].agg(["mean", "count"])
        by_emotion = by_emotion[by_emotion["count"] >= 2]
        if len(by_emotion) >= 2:
            best, worst = by_emotion["mean"].idxmax(), by_emotion["mean"].idxmin()
            insights.append(("info", f"Highest average confidence: **{best}** ({by_emotion.loc[best, 'mean']:.3f}); "
                                     f"lowest: **{worst}** ({by_emotion.loc[worst, 'mean']:.3f}) "
                                     "(emotions with at least 2 stories)."))
        top3_share = conf.round(3).value_counts().head(3).sum() / len(conf) * 100
        if len(conf) >= 15 and top3_share >= 50:
            insights.append(("warning", f"{top3_share:.0f}% of the confidence scores share just three distinct values, "
                                        "so the scores are heavily repeated; treat averages and correlations with care."))
    else:
        insights.append(("warning", "Not enough valid confidence values to summarise."))

    # City
    cities = frequency_table(df, "City")
    if not cities.empty:
        insights.append(("info", f"**{cities.iloc[0]['City']}** has the most weather-based stories "
                                 f"({int(cities.iloc[0]['Stories'])}); city is recorded for {int(cities['Stories'].sum())} "
                                 f"of {n} stories only."))
    else:
        insights.append(("warning", "No city information is available for the selected stories."))

    # Mode
    modes = frequency_table(df, "Mode")
    if not modes.empty:
        insights.append(("info", f"Most common story generation mode: **{modes.iloc[0]['Mode']}** "
                                 f"({modes.iloc[0]['Percent']:.1f}% of stories)."))

    # Multimedia
    if kpis["music_pct"] is not None:
        insights.append(("info", f"**{kpis['music_pct']:.1f}%** of stories have background music and "
                                 f"**{kpis['video_pct']:.1f}%** have a video."))
        both = df[(df["Background Music Added"] == True) & (df["Video Created"] == True)]  # noqa: E712
        insights.append(("info", f"{len(both)} stories have both background music and a video."))

    # Time trend
    daily = daily_counts(df)
    if len(daily) >= 2:
        peak = daily.loc[daily["Stories"].idxmax()]
        active_days = int((daily["Stories"] > 0).sum())
        insights.append(("info", f"Stories were created on {active_days} different day(s). Busiest day: "
                                 f"**{peak['Date']:%d %b %Y}** with {int(peak['Stories'])} stories."))
        monthly = monthly_counts(df)
        if len(monthly) >= 2:
            first, last = monthly.iloc[0], monthly.iloc[-1]
            insights.append(("info", f"Monthly volume went from {int(first['Stories'])} stories in {first['Month']} "
                                     f"to {int(last['Stories'])} in {last['Month']} (peak: "
                                     f"{monthly.loc[monthly['Stories'].idxmax(), 'Month']})."))
    else:
        insights.append(("warning", "Not enough distinct dates to describe a time trend."))

    # Correlation (never causation)
    pair = pairwise_correlation(df, "Temperature (C)", "Emotion Confidence")
    if pair["pearson"] is not None and pair["n"] >= 5:
        insights.append(("info", f"Temperature vs confidence: Pearson r = {pair['pearson']:.2f} "
                                 f"({describe_correlation(pair['pearson'])}), Spearman ρ = {pair['spearman']:.2f}, "
                                 f"based on only {pair['n']} stories that have a temperature. "
                                 "Correlation does not prove causation."))
    else:
        insights.append(("warning", f"Only {pair['n']} stories have both temperature and confidence, "
                                    "which is too few for a reliable correlation."))

    # Mode vs confidence
    if modes.shape[0] >= 2:
        by_mode = df.groupby("Mode")["Emotion Confidence"].agg(["mean", "count"])
        by_mode = by_mode[by_mode["count"] >= 2]
        if len(by_mode) >= 2:
            top_mode = by_mode["mean"].idxmax()
            insights.append(("info", f"**{top_mode}** stories have the higher average confidence "
                                     f"({by_mode.loc[top_mode, 'mean']:.3f}); this is a descriptive comparison, "
                                     "not proof that the mode causes higher confidence."))

    # Story length
    words = df["Story Word Count"].dropna()
    if len(words):
        insights.append(("info", f"Stories average **{words.mean():.0f} words** (shortest {int(words.min())}, "
                                 f"longest {int(words.max())})."))
    return insights


def kpi_sparklines(df: pd.DataFrame) -> Dict[str, Optional[List[float]]]:
    """Small daily series for the KPI-card sparklines (only days that have stories).

    A series is None when there are fewer than 2 active days, because one point is not a trend.
    """
    valid = df.dropna(subset=["Date"])
    if valid.empty:
        return {"stories": None, "confidence": None, "music": None, "video": None}
    daily = valid.groupby("Date")

    def pct_true(series: pd.Series) -> float:
        known = series.dropna()
        return known.astype(bool).mean() * 100 if len(known) else np.nan

    series = {
        "stories": daily.size().astype(float),
        "confidence": daily["Emotion Confidence"].mean(),
        "music": daily["Background Music Added"].apply(pct_true),
        "video": daily["Video Created"].apply(pct_true),
    }
    return {name: (values.dropna().round(3).tolist() if values.notna().sum() >= 2 else None)
            for name, values in series.items()}
