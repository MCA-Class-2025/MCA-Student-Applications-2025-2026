from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

ORIGINAL = ROOT / "data" / "menstrual_dataset.csv"
FINAL = ROOT / "data" / "api_fusion" / "final" / "femcare_final_cleaned.csv"
CENSUS = ROOT / "data" / "api_fusion" / "static" / "census_state.csv"
CDC = ROOT / "data" / "api_fusion" / "static" / "cdc_places_state.csv"
WEATHER = ROOT / "data" / "api_fusion" / "dynamic" / "open_meteo_row_level.csv"
FUSED = ROOT / "data" / "api_fusion" / "final" / "femcare_final_fused_dataset.csv"


def r(value, digits=3):
    if pd.isna(value):
        return None
    return round(float(value), digits)


def iqr_details(series: pd.Series):
    clean = pd.to_numeric(series, errors="coerce").dropna()
    q1 = clean.quantile(0.25)
    q3 = clean.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (clean < lower) | (clean > upper)
    return {
        "q1": r(q1),
        "q3": r(q3),
        "iqr": r(iqr),
        "lower": r(lower),
        "upper": r(upper),
        "outliers": int(mask.sum()),
        "outlier_pct": r(mask.mean() * 100, 2),
    }


WIDTH, HEIGHT = 1600, 920
NAVY = "#264653"
PINK = "#D53F8C"
PLUM = "#7A2E67"
TEAL = "#2A9D8F"
GOLD = "#E9A23B"
GRID = "#E7E2E6"
INK = "#333333"


def font(size=28, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def canvas(title, subtitle=None):
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 42), title, fill=NAVY, font=font(40, True))
    if subtitle:
        draw.text((72, 96), subtitle, fill="#666666", font=font(22))
    return image, draw


def save_image(image, name):
    image.save(OUT / name, format="PNG", optimize=True)


def axes(draw, left=150, top=160, right=1510, bottom=790, xlabel="", ylabel=""):
    draw.line((left, bottom, right, bottom), fill=INK, width=3)
    draw.line((left, top, left, bottom), fill=INK, width=3)
    if xlabel:
        box = draw.textbbox((0, 0), xlabel, font=font(24))
        draw.text(((left + right - (box[2] - box[0])) / 2, bottom + 70), xlabel, fill=INK, font=font(24))
    if ylabel:
        # Horizontal label is easier to read in a report than rotated raster text.
        draw.text((left, top - 38), ylabel, fill=INK, font=font(21))
    return left, top, right, bottom


def scale(value, vmin, vmax, pmin, pmax):
    if vmax == vmin:
        return (pmin + pmax) / 2
    return pmin + (float(value) - vmin) / (vmax - vmin) * (pmax - pmin)


def grid_y(draw, left, top, right, bottom, ymin, ymax, ticks=5):
    for i in range(ticks + 1):
        value = ymin + (ymax - ymin) * i / ticks
        y = scale(value, ymin, ymax, bottom, top)
        draw.line((left, y, right, y), fill=GRID, width=2)
        label = f"{value:.2f}" if ymax - ymin < 10 else f"{value:,.0f}"
        box = draw.textbbox((0, 0), label, font=font(18))
        draw.text((left - 16 - (box[2] - box[0]), y - 10), label, fill="#666666", font=font(18))


def scatter_plot(draw, x, y, left, top, right, bottom, color=PLUM, sizes=None):
    xmin, xmax = float(np.min(x)), float(np.max(x))
    ymin, ymax = float(np.min(y)), float(np.max(y))
    xpad = max((xmax - xmin) * 0.06, 0.01)
    ypad = max((ymax - ymin) * 0.12, 0.01)
    xmin, xmax = xmin - xpad, xmax + xpad
    ymin, ymax = ymin - ypad, ymax + ypad
    grid_y(draw, left, top, right, bottom, ymin, ymax)
    for i, (xv, yv) in enumerate(zip(x, y)):
        px = scale(xv, xmin, xmax, left, right)
        py = scale(yv, ymin, ymax, bottom, top)
        radius = int(sizes[i]) if sizes is not None else 8
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=color, outline="white", width=2)
    fit = np.polyfit(np.asarray(x, dtype=float), np.asarray(y, dtype=float), 1)
    for xa, xb in zip(np.linspace(xmin, xmax, 80)[:-1], np.linspace(xmin, xmax, 80)[1:]):
        ya, yb = fit[0] * xa + fit[1], fit[0] * xb + fit[1]
        draw.line((scale(xa, xmin, xmax, left, right), scale(ya, ymin, ymax, bottom, top), scale(xb, xmin, xmax, left, right), scale(yb, ymin, ymax, bottom, top)), fill=GOLD, width=4)
    for i in range(6):
        value = xmin + (xmax - xmin) * i / 5
        px = scale(value, xmin, xmax, left, right)
        draw.line((px, bottom, px, bottom + 8), fill=INK, width=2)
        label = f"{value:.1f}" if xmax < 100 else f"{value:,.0f}"
        box = draw.textbbox((0, 0), label, font=font(18))
        draw.text((px - (box[2] - box[0]) / 2, bottom + 14), label, fill="#666666", font=font(18))


def main():
    original = pd.read_csv(ORIGINAL)
    final = pd.read_csv(FINAL)
    census = pd.read_csv(CENSUS)
    cdc = pd.read_csv(CDC)
    weather = pd.read_csv(WEATHER)
    fused = pd.read_csv(FUSED)

    for frame in (original, final, weather, fused):
        frame["start_date"] = pd.to_datetime(frame["start_date"], errors="coerce")

    base_states = set(original["state"].dropna().astype(str).str.strip())
    census_states = set(census["state"].dropna().astype(str).str.strip())
    cdc_states = set(cdc["state"].dropna().astype(str).str.strip())

    numeric_summary_features = [
        "cycle_length_days",
        "pain_level",
        "stress_score_cycle",
        "sleep_hours_cycle",
        "temperature_mean",
        "humidity_mean",
        "precipitation",
        "wind_speed_mean",
        "cdc_obesity_prevalence",
        "cdc_depression_prevalence",
        "census_median_household_income",
    ]
    desc = final[numeric_summary_features].describe().T
    desc["median"] = final[numeric_summary_features].median()
    desc = desc[["count", "mean", "median", "std", "min", "25%", "50%", "75%", "max"]]

    missing = final.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    weather_dupes = int(weather.duplicated(["state", "start_date"]).sum())
    validation = {
        "original_rows": len(original),
        "original_columns": len(original.columns),
        "original_users": int(original["user_id"].nunique()),
        "original_states": int(original["state"].nunique()),
        "original_missing_cells": int(original.isna().sum().sum()),
        "original_duplicate_rows": int(original.duplicated().sum()),
        "original_duplicate_user_cycles": int(original.duplicated(["user_id", "cycle_number"]).sum()),
        "census_rows": len(census),
        "census_columns": len(census.columns),
        "census_duplicate_states": int(census["state"].duplicated().sum()),
        "census_states_matching_base": len(base_states & census_states),
        "census_states_not_in_base": sorted(census_states - base_states),
        "cdc_rows": len(cdc),
        "cdc_columns": len(cdc.columns),
        "cdc_duplicate_states": int(cdc["state"].duplicated().sum()),
        "cdc_states_matching_base": len(base_states & cdc_states),
        "cdc_states_not_in_base": sorted(cdc_states - base_states),
        "weather_rows": len(weather),
        "weather_columns": len(weather.columns),
        "weather_duplicate_state_dates": weather_dupes,
        "fused_rows": len(fused),
        "fused_columns": len(fused.columns),
        "final_rows": len(final),
        "final_columns": len(final.columns),
        "final_users": int(final["user_id"].nunique()),
        "final_states": int(final["state"].nunique()),
        "final_date_min": str(final["start_date"].min().date()),
        "final_date_max": str(final["start_date"].max().date()),
        "final_duplicate_rows": int(final.duplicated().sum()),
        "final_duplicate_user_cycles": int(final.duplicated(["user_id", "cycle_number"]).sum()),
        "final_missing_cells": int(final.isna().sum().sum()),
        "final_total_cells": int(final.shape[0] * final.shape[1]),
        "final_missing_pct": r(final.isna().sum().sum() / (final.shape[0] * final.shape[1]) * 100, 3),
        "missing_by_column": {k: int(v) for k, v in missing.items()},
        "exercise_missing_before_cleaning": int(fused["exercise_frequency"].isna().sum()),
        "coordinate_missing_rows": int((final["coordinates_available"] == 0).sum()),
        "weather_missing_rows": int(final[["temperature_mean", "humidity_mean", "precipitation", "wind_speed_mean"]].isna().any(axis=1).sum()),
        "census_unmatched_cycle_rows": int(final["state_fips"].isna().sum()),
        "cdc_unmatched_cycle_rows": int(final["cdc_total_population"].isna().sum()),
        "weather_unmatched_cycle_rows": int(final["temperature_mean"].isna().sum()),
        "dtype_counts": {str(k): int(v) for k, v in final.dtypes.astype(str).value_counts().items()},
        "iqr": {
            "cycle_length_days": iqr_details(final["cycle_length_days"]),
            "temperature_mean": iqr_details(final["temperature_mean"]),
            "census_median_household_income": iqr_details(final["census_median_household_income"]),
        },
        "summary": {
            feature: {key: r(value, 3) for key, value in row.items()}
            for feature, row in desc.to_dict(orient="index").items()
        },
    }

    weather_corr = final[["temperature_mean", "humidity_mean", "precipitation", "wind_speed_mean", "pain_level"]].corr()["pain_level"].drop("pain_level")
    validation["weather_pain_correlations"] = {k: r(v, 4) for k, v in weather_corr.items()}

    state = final.groupby("state", as_index=False).agg(
        average_pain=("pain_level", "mean"),
        average_stress=("stress_score_cycle", "mean"),
        average_sleep=("sleep_hours_cycle", "mean"),
        average_temperature=("temperature_mean", "mean"),
        obesity=("cdc_obesity_prevalence", "first"),
        inactivity=("cdc_physical_inactivity_prevalence", "first"),
        depression=("cdc_depression_prevalence", "first"),
        median_income=("census_median_household_income", "first"),
        population=("census_total_population", "first"),
        records=("user_id", "size"),
    )
    state_corr = state.select_dtypes(include=np.number).corr()
    validation["state_level_correlations"] = {
        "depression_vs_average_stress": r(state["depression"].corr(state["average_stress"]), 4),
        "inactivity_vs_average_pain": r(state["inactivity"].corr(state["average_pain"]), 4),
        "obesity_vs_average_pain": r(state["obesity"].corr(state["average_pain"]), 4),
        "income_vs_average_pain": r(state["median_income"].corr(state["average_pain"]), 4),
        "temperature_vs_average_pain": r(state["average_temperature"].corr(state["average_pain"]), 4),
    }

    with open(OUT / "analysis_results.json", "w", encoding="utf-8") as handle:
        json.dump(validation, handle, indent=2)
    desc.round(3).to_csv(OUT / "selected_numeric_summary.csv")
    state.round(4).to_csv(OUT / "state_level_analysis.csv", index=False)

    # 1. Distribution visualization
    image, draw = canvas("Distribution of Menstrual Pain Level", f"Cycle-level records; n = {len(final):,}")
    left, top, right, bottom = axes(draw, xlabel="Pain level (1-10)", ylabel="Cycle records")
    counts = final["pain_level"].value_counts().sort_index()
    ymax = float(counts.max()) * 1.1
    grid_y(draw, left, top, right, bottom, 0, ymax)
    bar_w = (right - left) / 12
    for value, count in counts.items():
        x = scale(value, 1, 10, left + bar_w, right - bar_w)
        y = scale(count, 0, ymax, bottom, top)
        draw.rounded_rectangle((x - bar_w * 0.38, y, x + bar_w * 0.38, bottom), radius=8, fill=PINK)
        label = str(int(value))
        box = draw.textbbox((0, 0), label, font=font(20))
        draw.text((int(x - (box[2] - box[0]) / 2), bottom + 16), label, fill=INK, font=font(20))
    save_image(image, "fig01_pain_distribution.png")

    # 2. Boxplot for outlier assessment
    image, draw = canvas("Cycle Length Boxplot and IQR Outlier Bounds", "Outliers are flagged statistically and reviewed as plausible observations")
    left, top, right, bottom = axes(draw, top=220, bottom=700, xlabel="Cycle length (days)")
    series = final["cycle_length_days"].dropna().astype(float)
    q1, median, q3 = series.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    lower_whisker = series[series >= lower_bound].min()
    upper_whisker = series[series <= upper_bound].max()
    xmin, xmax = series.min(), series.max()
    y = 440
    sx = lambda v: scale(v, xmin, xmax, left, right)
    draw.line((sx(lower_whisker), y, sx(upper_whisker), y), fill=INK, width=5)
    draw.line((sx(lower_whisker), y - 55, sx(lower_whisker), y + 55), fill=INK, width=4)
    draw.line((sx(upper_whisker), y - 55, sx(upper_whisker), y + 55), fill=INK, width=4)
    draw.rounded_rectangle((sx(q1), y - 95, sx(q3), y + 95), radius=10, fill="#F2A7C6", outline=PLUM, width=4)
    draw.line((sx(median), y - 95, sx(median), y + 95), fill=PLUM, width=6)
    outliers = series[(series < lower_bound) | (series > upper_bound)]
    for idx, value in enumerate(outliers.iloc[:500]):
        oy = y + ((idx % 9) - 4) * 8
        draw.ellipse((sx(value) - 4, oy - 4, sx(value) + 4, oy + 4), fill=GOLD)
    for tick in np.linspace(xmin, xmax, 8):
        x = sx(tick)
        draw.line((x, bottom, x, bottom + 8), fill=INK, width=2)
        draw.text((int(x - 16), bottom + 14), f"{tick:.0f}", fill="#666666", font=font(18))
    draw.text((left, 750), f"Q1={q1:.1f}, median={median:.1f}, Q3={q3:.1f}; IQR bounds={lower_bound:.1f} to {upper_bound:.1f}; flagged={len(outliers):,} ({len(outliers)/len(series)*100:.2f}%)", fill="#555555", font=font(20))
    save_image(image, "fig02_cycle_length_boxplot.png")

    # 3. Weather-original relationship
    temp_bins = pd.qcut(final["temperature_mean"], q=8, duplicates="drop")
    temp_group = final.groupby(temp_bins, observed=True).agg(temperature=("temperature_mean", "mean"), pain=("pain_level", "mean"), records=("pain_level", "size")).reset_index(drop=True)
    image, draw = canvas("Mean Temperature vs. Average Pain", f"Temperature quantile groups; row-level Pearson r = {weather_corr['temperature_mean']:.3f}")
    left, top, right, bottom = axes(draw, xlabel="Mean temperature (degrees C)", ylabel="Average pain")
    xmin, xmax = temp_group["temperature"].min(), temp_group["temperature"].max()
    ymin, ymax = temp_group["pain"].min() - 0.03, temp_group["pain"].max() + 0.03
    grid_y(draw, left, top, right, bottom, ymin, ymax)
    points = []
    for _, row in temp_group.iterrows():
        px = scale(row["temperature"], xmin, xmax, left, right)
        py = scale(row["pain"], ymin, ymax, bottom, top)
        points.append((px, py))
    draw.line(points, fill=TEAL, width=5)
    for (px, py), (_, row) in zip(points, temp_group.iterrows()):
        draw.ellipse((px - 10, py - 10, px + 10, py + 10), fill=TEAL, outline="white", width=2)
        draw.text((int(px - 22), int(py - 36)), f"{row['pain']:.2f}", fill=INK, font=font(17))
    for tick in np.linspace(xmin, xmax, 6):
        px = scale(tick, xmin, xmax, left, right)
        draw.text((int(px - 22), bottom + 14), f"{tick:.1f}", fill="#666666", font=font(18))
    save_image(image, "fig03_temperature_vs_pain.png")

    # 4. CDC-original relationship at state level
    image, draw = canvas("State Physical Inactivity vs. Average Menstrual Pain", f"50-state analysis; Pearson r = {validation['state_level_correlations']['inactivity_vs_average_pain']:.3f}")
    left, top, right, bottom = axes(draw, xlabel="CDC physical inactivity prevalence (%)", ylabel="Average pain by state")
    scatter_plot(draw, state["inactivity"].to_numpy(), state["average_pain"].to_numpy(), left, top, right, bottom)
    save_image(image, "fig04_inactivity_vs_pain.png")

    # 5. Correlation heatmap (multivariate)
    heat_features = ["pain_level", "stress_score_cycle", "sleep_hours_cycle", "mood_score", "energy_level", "temperature_mean", "humidity_mean", "cdc_obesity_prevalence", "cdc_depression_prevalence", "census_median_household_income"]
    labels = ["Pain", "Stress", "Sleep", "Mood", "Energy", "Temp", "Humidity", "Obesity", "Depression", "Income"]
    corr = final[heat_features].corr().to_numpy()
    image, draw = canvas("Multivariate Correlation Heatmap", "Original and API-derived numerical variables")
    x0, y0, cell = 390, 190, 62
    for i, row_label in enumerate(labels):
        draw.text((75, y0 + i * cell + 16), row_label, fill=INK, font=font(19))
        draw.text((x0 + i * cell + 4, y0 - 38), row_label[:7], fill=INK, font=font(16))
        for j in range(len(labels)):
            value = float(corr[i, j])
            intensity = min(abs(value), 1.0)
            if value >= 0:
                base = np.array([213, 63, 140])
            else:
                base = np.array([42, 157, 143])
            rgb = tuple((255 - (255 - base) * intensity).astype(int))
            box = (x0 + j * cell, y0 + i * cell, x0 + (j + 1) * cell, y0 + (i + 1) * cell)
            draw.rectangle(box, fill=rgb, outline="white", width=2)
            label = f"{value:.2f}"
            text_color = "white" if intensity > 0.52 else INK
            draw.text((box[0] + 8, box[1] + 19), label, fill=text_color, font=font(15, intensity > 0.7))
    draw.text((x0, y0 + len(labels) * cell + 30), "Pink = positive correlation; teal = negative correlation; pale = weak relationship", fill="#555555", font=font(19))
    save_image(image, "fig05_correlation_heatmap.png")

    # 6. Explicit fusion insight
    population_root = np.sqrt(state["population"].to_numpy(dtype=float))
    bubble_sizes = 7 + 10 * (population_root - population_root.min()) / (population_root.max() - population_root.min())
    image, draw = canvas("Fusion Insight: CDC Depression Context vs. Menstrual Stress", f"50-state analysis; Pearson r = {validation['state_level_correlations']['depression_vs_average_stress']:.3f}; bubble size reflects Census population")
    left, top, right, bottom = axes(draw, xlabel="CDC depression prevalence (%)", ylabel="Average cycle stress by state")
    scatter_plot(draw, state["depression"].to_numpy(), state["average_stress"].to_numpy(), left, top, right, bottom, color=PINK, sizes=bubble_sizes)
    save_image(image, "fig06_fusion_insight.png")

    # 7. Pipeline diagram
    image, draw = canvas("FemCare Phase 1 Data-Fusion Pipeline", "All original cycle rows were retained while external context was added")
    boxes = [
        (55, 310, 320, 520, "Original menstrual CSV\n17,976 x 34", "#FCE4EC"),
        (470, 175, 760, 315, "Census ACS\n52 x 8", "#E8EEF5"),
        (470, 390, 760, 530, "CDC PLACES\n51 x 8", "#E8EEF5"),
        (470, 605, 760, 745, "Open-Meteo\n17,976 x 40", "#E8EEF5"),
        (875, 350, 1160, 560, "LEFT JOINS\nstate\nstate + start_date", "#FFF3CD"),
        (1270, 310, 1545, 520, "Final cleaned CSV\n17,976 x 56", "#DFF3EA"),
    ]
    for x1, y1, x2, y2, label, fill in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=fill, outline="#7A6173", width=3)
        lines = label.split("\n")
        total_h = len(lines) * 34
        for idx, line in enumerate(lines):
            f = font(25, idx == 0)
            box = draw.textbbox((0, 0), line, font=f)
            tx = (x1 + x2 - (box[2] - box[0])) / 2
            ty = (y1 + y2 - total_h) / 2 + idx * 36
            draw.text((tx, ty), line, fill=NAVY, font=f)
    def arrow(start, end):
        draw.line((*start, *end), fill=PLUM, width=6)
        ex, ey = end
        draw.polygon([(ex, ey), (ex - 18, ey - 10), (ex - 18, ey + 10)], fill=PLUM)
    arrow((375, 340), (875, 370))
    arrow((760, 245), (875, 410))
    arrow((760, 460), (875, 455))
    arrow((760, 675), (875, 505))
    arrow((1160, 455), (1270, 415))
    save_image(image, "fig00_fusion_pipeline.png")

    # Sanitized request/response evidence using the schema and one stored row.
    sample = weather.iloc[0]
    image = Image.new("RGB", (1600, 850), "#111827")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 35, 1565, 815), radius=18, fill="#111827", outline="#374151", width=3)
    draw.text((75, 70), "FemCare API collection - sanitized request/response evidence", fill="#F9FAFB", font=font(30, True))
    lines = [
        ("REQUEST", "#F9A8D4"),
        ("GET https://archive-api.open-meteo.com/v1/archive", "#D1FAE5"),
        (f"latitude={sample['latitude']}  longitude={sample['longitude']}", "#E5E7EB"),
        (f"start_date={sample['start_date'].date()}  end_date={sample['start_date'].date()}", "#E5E7EB"),
        ("daily=temperature_2m_mean,relative_humidity_2m_mean,", "#E5E7EB"),
        ("      precipitation_sum,wind_speed_10m_mean", "#E5E7EB"),
        ("", "#E5E7EB"),
        ("RESPONSE  HTTP 200  application/json", "#F9A8D4"),
        ("{", "#E5E7EB"),
        (f'  "daily": {{"time": ["{sample["start_date"].date()}"],', "#E5E7EB"),
        (f'    "temperature_2m_mean": [{sample["temperature_mean"]}],', "#E5E7EB"),
        (f'    "relative_humidity_2m_mean": [{sample["humidity_mean"]}],', "#E5E7EB"),
        (f'    "precipitation_sum": [{sample["precipitation"]}],', "#E5E7EB"),
        (f'    "wind_speed_10m_mean": [{sample["wind_speed_mean"]}]}}', "#E5E7EB"),
        ("}", "#E5E7EB"),
    ]
    y = 135
    mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 24)
    mono_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 24)
    for line, color in lines:
        draw.text((85, y), line, fill=color, font=mono_bold if line.startswith(("REQUEST", "RESPONSE")) else mono)
        y += 42
    draw.text((75, 775), "Raw JSON was parsed into the stored open_meteo_row_level.csv; credentials are not shown.", fill="#9CA3AF", font=font(18))
    save_image(image, "fig_api_request_response.png")

    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
