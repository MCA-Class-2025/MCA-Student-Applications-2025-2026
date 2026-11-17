"""Per-chart filters.

Every chart (and every table / summary card) gets its OWN "Filter" button.
A filter only changes the data given to that one card, never the other cards.

apply_filters() is plain pandas (easy to test); chart_filter() draws the
Streamlit popover with the filter widgets.
"""

from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import streamlit as st

# Column in the processed data -> label shown in the filter popover
FILTER_LABELS: Dict[str, str] = {
    "Language": "Language",
    "Detected Emotion": "Emotion",
    "Mode": "Mode",
    "City": "City",
    "Weather Condition": "Weather",
    "Music Label": "Background music",
    "Video Label": "Video",
}
STANDARD_FIELDS: List[str] = ["Language", "Detected Emotion", "Mode", "Music Label", "Video Label"]
WEATHER_FIELDS: List[str] = ["Language", "Detected Emotion", "Mode", "City", "Weather Condition"]
ALL_FIELDS: List[str] = list(FILTER_LABELS)


def _date_bounds(value) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Turn what st.date_input returns (one date or a 1-2 item tuple) into (start, end)."""
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            return pd.Timestamp(value[0]), pd.Timestamp(value[1])
        return pd.Timestamp(value[0]), pd.Timestamp(value[0])   # user is still choosing the end date
    return pd.Timestamp(value), pd.Timestamp(value)


def apply_filters(df: pd.DataFrame, selections: Dict[str, Sequence[str]], date_value=None,
                  full_bounds=None) -> pd.DataFrame:
    """Return the rows that match the selections.

    An empty selection means "all values". Rows without a valid date are kept
    only while the complete date range is selected.
    """
    mask = pd.Series(True, index=df.index)
    for column, selected in selections.items():
        if selected:
            mask &= df[column].isin(selected)
    if date_value is not None and full_bounds is not None:
        start, end = _date_bounds(date_value)
        covers_all = start.date() <= full_bounds[0] and end.date() >= full_bounds[1]
        mask &= df["Date"].between(start, end) | (df["Date"].isna() & covers_all)
    return df[mask].copy()


def reset_scope(prefix: str) -> None:
    """Callback: forget every stored value whose key starts with prefix."""
    for key in [k for k in st.session_state if k.startswith(prefix)]:
        del st.session_state[key]


def reset_all_filters() -> None:
    """Callback: reset the filters of every chart at once."""
    reset_scope("flt_")


def _count_active(prefix: str, bounds) -> int:
    """How many filters of this card are currently active (for the button label)."""
    active = 0
    for key, value in st.session_state.items():
        if not key.startswith(prefix):
            continue
        if key.startswith(prefix + "ms_") and value:
            active += 1
        elif key == prefix + "date" and bounds is not None and isinstance(value, (tuple, list)):
            if len(value) == 2 and (value[0], value[1]) != bounds:
                active += 1
    return active


def chart_filter(df_all: pd.DataFrame, scope: str, dataset_id: str, fields: Sequence[str],
                 use_date: bool = True,
                 extras: Optional[Callable[[str], dict]] = None) -> Tuple[pd.DataFrame, dict, int]:
    """Draw a 'Filter' popover for one card and return (filtered_df, extra_options, active_count).

    scope      unique name of the card (e.g. 'bar_language')
    extras     optional function(prefix) that draws extra widgets (e.g. a category
               selector) inside the popover and returns a dict of options
    """
    prefix = f"flt_{dataset_id}_{scope}_"
    dates = df_all["Date"].dropna()
    bounds = (dates.min().date(), dates.max().date()) if (use_date and not dates.empty) else None
    active = _count_active(prefix, bounds)

    selections: Dict[str, list] = {}
    date_value, options = None, {}
    with st.popover("Filter" if not active else f"Filter · {active}", icon=":material/filter_list:"):
        st.caption("Applies to this chart only. Leave empty to include all.")
        for column in fields:
            choices = sorted(df_all[column].dropna().unique().tolist())
            selections[column] = st.multiselect(FILTER_LABELS[column], choices, key=f"{prefix}ms_{column}",
                                                placeholder="All")
        if bounds is not None:
            date_value = st.date_input("Date range", value=bounds, min_value=bounds[0], max_value=bounds[1],
                                       key=f"{prefix}date")
        if extras is not None:
            options = extras(prefix)
        st.button("Reset this filter", key=f"btn_{dataset_id}_{scope}", on_click=reset_scope, args=(prefix,),
                  width="stretch")
    return apply_filters(df_all, selections, date_value, bounds), options, active
