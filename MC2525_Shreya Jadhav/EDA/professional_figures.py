"""Presentation-ready, reproducible static figures for the fused dataset."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PLUM = "#50314F"
PINK = "#D63384"
PURPLE = "#7753B7"
TEAL = "#178F82"
CORAL = "#F07A80"
GOLD = "#E8AB47"
INK = "#302B37"
MUTED = "#736A78"


def _canvas(title: str, subtitle: str, size=(10.5, 6.2)):
    fig, ax = plt.subplots(figsize=size, facecolor="#FBF8FA")
    ax.set_facecolor("#FFFFFF")
    fig.subplots_adjust(left=0.11, right=0.94, top=0.78, bottom=0.15)
    fig.text(0.11, 0.94, title, fontsize=19, fontweight="bold", color=INK)
    fig.text(0.11, 0.89, subtitle, fontsize=10.5, color=MUTED)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="y", color="#EDE6ED", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0, labelsize=10, pad=7)
    return fig, ax


def _save(fig, output: Path, name: str):
    fig.savefig(output / name, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def render_professional_figures(df: pd.DataFrame, output: str | Path) -> None:
    """Replace basic EDA PNGs with a coordinated set of analytical figures."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, ax = _canvas("Cycle lengths cluster around four weeks", "Distribution of recorded cycle lengths · n = {:,}".format(len(df)))
    sns.histplot(df["cycle_length_days"].dropna(), bins=23, color=PURPLE, edgecolor="white", ax=ax)
    ax.axvline(df["cycle_length_days"].median(), color=PINK, lw=2, ls="--", label=f"Median {df['cycle_length_days'].median():.0f} days")
    ax.set(xlabel="Cycle length (days)", ylabel="Cycle records")
    ax.legend(frameon=False, labelcolor=INK)
    _save(fig, output, "01_cycle_length_distribution.png")

    fig, ax = _canvas("Recorded pain spans the full scale", "Count of cycle records by pain score · 7–10 highlighted")
    counts = df["pain_level"].value_counts().sort_index()
    bars = ax.bar(counts.index.astype(str), counts.values, color=[CORAL if x >= 7 else PURPLE for x in counts.index], width=.72)
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=3, fontsize=8, color=MUTED)
    ax.set(xlabel="Pain score (0–10)", ylabel="Cycle records")
    _save(fig, output, "02_pain_level_distribution.png")

    fig, ax = _canvas("Flow-level composition", "Share of cycle records by reported flow")
    flow = df["flow_level"].value_counts().reindex(["Light", "Medium", "Heavy"]).fillna(0)
    wedges, _ = ax.pie(flow, colors=[TEAL, GOLD, CORAL], startangle=90, wedgeprops={"width": .31, "edgecolor": "white", "linewidth": 3})
    ax.text(0, .08, f"{flow.sum():,.0f}", ha="center", va="center", fontsize=22, fontweight="bold", color=INK)
    ax.text(0, -.13, "cycle records", ha="center", va="center", fontsize=10, color=MUTED)
    ax.legend(wedges, [f"{name} · {value/flow.sum():.1%}" for name, value in flow.items()], loc="center left", bbox_to_anchor=(1.02, .5), frameon=False)
    _save(fig, output, "03_flow_level_distribution.png")

    fig, ax = _canvas("Reported cycle phases", "Recorded phase labels in the fused dataset")
    phase = df["cycle_phase"].value_counts().sort_values()
    bars = ax.barh(phase.index, phase.values, color=[TEAL, PURPLE, PINK, CORAL][:len(phase)])
    ax.bar_label(bars, labels=[f"{v:,}" for v in phase.values], padding=5, color=INK, fontsize=10)
    ax.set(xlabel="Cycle records", ylabel="")
    ax.grid(axis="x", color="#EDE6ED")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, phase.max()*1.18)
    _save(fig, output, "04_cycle_phase_distribution.png")

    for number, field, title, ylab, color in [
        (5, "stress_score_cycle", "Stress rises with recorded pain", "Average stress score", PURPLE),
        (6, "sleep_hours_cycle", "Sleep differs across pain scores", "Average sleep (hours)", TEAL),
        (7, "mood_score", "Mood differs across pain scores", "Average mood score", PINK),
        (8, "energy_level", "Energy differs across pain scores", "Average energy score", GOLD),
    ]:
        grouped = df.groupby("pain_level")[field].agg(["mean", "count", "std"])
        grouped["se"] = grouped["std"] / np.sqrt(grouped["count"])
        fig, ax = _canvas(title, "Mean and 95% confidence interval by recorded pain level · descriptive association")
        x = grouped.index.to_numpy(dtype=float)
        y = grouped["mean"].to_numpy(dtype=float)
        ci = 1.96 * grouped["se"].fillna(0).to_numpy(dtype=float)
        ax.plot(x, y, color=color, lw=3, marker="o", ms=7)
        ax.fill_between(x, y-ci, y+ci, color=color, alpha=.15, linewidth=0)
        ax.set(xlabel="Pain score (0–10)", ylabel=ylab)
        ax.set_xticks(x)
        _save(fig, output, f"{number:02d}_pain_vs_{field.replace('_score_cycle','').replace('_hours_cycle','').replace('_score','').replace('_level','')}.png")

    candidates = ["work_hours_lost", "stress_score_cycle", "sleep_hours_cycle", "mood_score", "energy_level", "concentration_score", "overall_health_score", "cycle_length_days", "temperature_mean"]
    corr = df[["pain_level", *candidates]].corr(numeric_only=True)["pain_level"].drop("pain_level").dropna()
    corr = corr.reindex(corr.abs().sort_values().index)
    fig, ax = _canvas("Which measures track with pain?", "Pearson correlation · association does not imply causation", size=(11, 6.6))
    bars = ax.barh(corr.index.str.replace("_", " ").str.title(), corr.values, color=[PINK if value > 0 else TEAL for value in corr])
    ax.axvline(0, color=MUTED, lw=1)
    ax.bar_label(bars, labels=[f"{v:+.2f}" for v in corr], padding=4, fontsize=9, color=INK)
    ax.set(xlabel="Correlation with pain score", ylabel="")
    ax.set_xlim(-1.08, 1.08)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#EDE6ED")
    fig.subplots_adjust(left=.27, right=.91, top=.78, bottom=.15)
    _save(fig, output, "09_top_pain_correlations.png")
