"""Pure helpers for the MenoCare session-only symptom tracker.

This module summarizes self-reported entries. It does not diagnose menopause,
calculate a clinical risk score, or recommend treatment.
"""

from __future__ import annotations

from datetime import date, datetime
from html import escape

import pandas as pd


SYMPTOM_FIELDS = {
    "hot_flashes": "Hot flashes",
    "night_sweats": "Night sweats",
    "sleep_disruption": "Sleep disruption",
    "low_mood_anxiety": "Low mood or anxiety",
    "brain_fog": "Memory or concentration difficulty",
    "fatigue": "Fatigue",
    "joint_discomfort": "Joint or muscle discomfort",
    "vaginal_dryness": "Vaginal dryness or discomfort",
    "urinary_symptoms": "Urinary symptoms",
}

SEVERITY_LABELS = {
    0: "None",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Very severe",
}

BLEEDING_OPTIONS = ("None", "Spotting", "Light", "Moderate", "Heavy")
MENSTRUAL_STATUS_OPTIONS = (
    "Periods continuing or changing",
    "No period for less than 12 months",
    "No period for 12 months or more",
    "Periods absent after hysterectomy or other procedure",
    "Unsure",
)
MEDICATION_CHANGE_OPTIONS = (
    "Started",
    "Stopped",
    "Dose changed",
    "Missed dose",
    "Other change",
)


def create_entry(
    *,
    entry_date: date,
    menstrual_status: str,
    bleeding: str,
    symptoms: dict[str, int],
    daily_impact: int,
    hourly_soaking_over_two_hours: bool = False,
    concerning_bleeding_symptoms: bool = False,
    severe_sudden_pain: bool = False,
    notes: str = "",
) -> dict:
    """Validate and normalize a user-entered daily check-in."""
    if menstrual_status not in MENSTRUAL_STATUS_OPTIONS:
        raise ValueError("Choose a valid menstrual-status option.")
    if bleeding not in BLEEDING_OPTIONS:
        raise ValueError("Choose a valid bleeding option.")
    if not 0 <= int(daily_impact) <= 4:
        raise ValueError("Daily impact must be between 0 and 4.")

    normalized_symptoms = {}
    for field in SYMPTOM_FIELDS:
        value = int(symptoms.get(field, 0))
        if not 0 <= value <= 4:
            raise ValueError(f"{SYMPTOM_FIELDS[field]} must be between 0 and 4.")
        normalized_symptoms[field] = value

    return {
        "entry_date": entry_date.isoformat(),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "menstrual_status": menstrual_status,
        "bleeding": bleeding,
        **normalized_symptoms,
        "daily_impact": int(daily_impact),
        "hourly_soaking_over_two_hours": bool(hourly_soaking_over_two_hours),
        "concerning_bleeding_symptoms": bool(concerning_bleeding_symptoms),
        "severe_sudden_pain": bool(severe_sudden_pain),
        "notes": notes.strip()[:1000],
    }


def create_quick_check_in(
    *,
    entry_date: date,
    selected_symptoms: list[str],
    symptom_severity: int,
    daily_impact: int,
    notes: str = "",
) -> dict:
    """Create a short daily entry using one shared symptom intensity.

    This is intentionally a quick reflection. Users can record a specific
    episode with its own severity and duration through an event log.
    """
    unknown = set(selected_symptoms).difference(SYMPTOM_FIELDS)
    if unknown:
        raise ValueError("Choose symptoms from the available list.")
    if not 0 <= int(symptom_severity) <= 4:
        raise ValueError("Symptom intensity must be between 0 and 4.")
    if not selected_symptoms and int(symptom_severity) != 0:
        raise ValueError("Choose at least one symptom before setting an intensity.")
    if selected_symptoms and int(symptom_severity) == 0:
        raise ValueError("Choose an intensity of at least Mild for the selected symptoms.")
    symptoms = {
        field: int(symptom_severity) if field in selected_symptoms else 0
        for field in SYMPTOM_FIELDS
    }
    return create_entry(
        entry_date=entry_date,
        menstrual_status="Unsure",
        bleeding="None",
        symptoms=symptoms,
        daily_impact=daily_impact,
        notes=notes,
    )


def create_symptom_event(
    *,
    event_date: date,
    symptom: str,
    severity: int,
    duration_minutes: int | None = None,
    possible_trigger: str = "",
    notes: str = "",
) -> dict:
    """Create one symptom episode without interpreting its medical cause."""
    if symptom not in SYMPTOM_FIELDS:
        raise ValueError("Choose a valid symptom.")
    if not 1 <= int(severity) <= 4:
        raise ValueError("Symptom-event severity must be between 1 and 4.")
    if duration_minutes is not None and int(duration_minutes) < 0:
        raise ValueError("Duration cannot be negative.")
    return {
        "event_date": event_date.isoformat(),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "Symptom episode",
        "event_name": SYMPTOM_FIELDS[symptom],
        "severity": int(severity),
        "duration_minutes": int(duration_minutes) if duration_minutes is not None else None,
        "menstrual_status": "",
        "bleeding": "",
        "change_type": "",
        "hourly_soaking_over_two_hours": False,
        "concerning_bleeding_symptoms": False,
        "severe_sudden_pain": False,
        "details": possible_trigger.strip()[:300],
        "notes": notes.strip()[:1000],
    }


def create_bleeding_event(
    *,
    event_date: date,
    menstrual_status: str,
    bleeding: str,
    hourly_soaking_over_two_hours: bool = False,
    concerning_bleeding_symptoms: bool = False,
    severe_sudden_pain: bool = False,
    notes: str = "",
) -> dict:
    """Create a bleeding event with fields required by the safety rules."""
    if menstrual_status not in MENSTRUAL_STATUS_OPTIONS:
        raise ValueError("Choose a valid menstrual-status option.")
    if bleeding not in BLEEDING_OPTIONS or bleeding == "None":
        raise ValueError("Choose the bleeding type that occurred.")
    return {
        "event_date": event_date.isoformat(),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "Bleeding",
        "event_name": f"{bleeding} bleeding",
        "severity": None,
        "duration_minutes": None,
        "menstrual_status": menstrual_status,
        "bleeding": bleeding,
        "change_type": "",
        "hourly_soaking_over_two_hours": bool(hourly_soaking_over_two_hours),
        "concerning_bleeding_symptoms": bool(concerning_bleeding_symptoms),
        "severe_sudden_pain": bool(severe_sudden_pain),
        "details": "",
        "notes": notes.strip()[:1000],
    }


def create_medication_event(
    *,
    event_date: date,
    medication_name: str,
    change_type: str,
    notes: str = "",
) -> dict:
    """Record a medication change without giving medication advice."""
    name = medication_name.strip()
    if not name:
        raise ValueError("Enter the medication or supplement name.")
    if change_type not in MEDICATION_CHANGE_OPTIONS:
        raise ValueError("Choose a valid medication-change type.")
    return {
        "event_date": event_date.isoformat(),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "Medication change",
        "event_name": name[:150],
        "severity": None,
        "duration_minutes": None,
        "menstrual_status": "",
        "bleeding": "",
        "change_type": change_type,
        "hourly_soaking_over_two_hours": False,
        "concerning_bleeding_symptoms": False,
        "severe_sudden_pain": False,
        "details": "",
        "notes": notes.strip()[:1000],
    }


def safety_notices(entry: dict) -> list[dict[str, str]]:
    """Return conservative care messages for a few explicit red flags.

    The rules are transparent and intentionally limited; no absence of a notice
    means that an entry is medically safe.
    """
    notices = []
    if entry.get("severe_sudden_pain"):
        notices.append({
            "level": "emergency",
            "title": "Severe or sudden pain needs urgent assessment",
            "message": "Seek urgent medical care now, especially if the pain is new, intense, or worsening. Contact local emergency services if you feel seriously unwell.",
        })
    if entry.get("hourly_soaking_over_two_hours") and entry.get("concerning_bleeding_symptoms"):
        notices.append({
            "level": "emergency",
            "title": "Heavy bleeding with concerning symptoms",
            "message": "Seek emergency medical care now. Contact local emergency services if you have chest pain, shortness of breath, faintness, or marked dizziness.",
        })
    elif entry.get("hourly_soaking_over_two_hours"):
        notices.append({
            "level": "urgent",
            "title": "Very heavy bleeding",
            "message": "Contact a healthcare professional urgently for advice. If you become dizzy, faint, short of breath, or develop chest pain, seek emergency care.",
        })

    if (
        entry.get("menstrual_status") == "No period for 12 months or more"
        and entry.get("bleeding") != "None"
    ):
        notices.append({
            "level": "prompt",
            "title": "Bleeding after 12 months without a period",
            "message": "Arrange a medical assessment promptly, even if this happened once or was only spotting. Many causes are not serious, but it should always be checked.",
        })
    return notices


def event_safety_notices(event: dict) -> list[dict[str, str]]:
    """Apply the existing transparent bleeding rules to a bleeding event."""
    if event.get("event_type") != "Bleeding":
        return []
    return safety_notices(event)


def entries_frame(entries: list[dict]) -> pd.DataFrame:
    """Return normalized entries sorted by date for charts and download."""
    columns = [
        "entry_date", "saved_at", "menstrual_status", "bleeding",
        *SYMPTOM_FIELDS.keys(), "daily_impact",
        "hourly_soaking_over_two_hours", "concerning_bleeding_symptoms",
        "severe_sudden_pain", "notes",
    ]
    if not entries:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame(entries).reindex(columns=columns)
    frame["entry_date"] = pd.to_datetime(frame["entry_date"], errors="coerce")
    for field in (*SYMPTOM_FIELDS.keys(), "daily_impact"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame.sort_values(["entry_date", "saved_at"]).reset_index(drop=True)


def events_frame(events: list[dict]) -> pd.DataFrame:
    """Return session events in a consistent, exportable order."""
    columns = [
        "event_date", "saved_at", "event_type", "event_name", "severity",
        "duration_minutes", "menstrual_status", "bleeding", "change_type",
        "hourly_soaking_over_two_hours", "concerning_bleeding_symptoms",
        "severe_sudden_pain", "details", "notes",
    ]
    if not events:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame(events).reindex(columns=columns)
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="coerce")
    return frame.sort_values(["event_date", "saved_at"]).reset_index(drop=True)


def trend_summary(frame: pd.DataFrame) -> dict:
    """Describe logged data without converting it into a medical score."""
    if frame.empty:
        return {
            "entries": 0,
            "days_logged": 0,
            "latest_date": None,
            "most_logged_symptom": None,
            "most_logged_symptom_mean": None,
        }
    means = frame[list(SYMPTOM_FIELDS)].mean().dropna()
    highest = means.idxmax() if len(means) else None
    return {
        "entries": len(frame),
        "days_logged": frame["entry_date"].dt.date.nunique(),
        "latest_date": frame["entry_date"].max().date(),
        "most_logged_symptom": SYMPTOM_FIELDS.get(highest) if highest else None,
        "most_logged_symptom_mean": round(float(means[highest]), 1) if highest else None,
    }


def period_summary(
    check_ins: pd.DataFrame,
    events: pd.DataFrame,
    frequency: str = "weekly",
) -> pd.DataFrame:
    """Aggregate logged activity by calendar week or month.

    Values remain descriptive counts and means; this is not a clinical score.
    """
    if frequency not in {"weekly", "monthly"}:
        raise ValueError("Frequency must be weekly or monthly.")
    period_code = "W-SUN" if frequency == "weekly" else "M"
    rows: dict[str, dict] = {}

    if not check_ins.empty:
        working = check_ins.copy()
        working["period"] = working["entry_date"].dt.to_period(period_code)
        for period, group in working.groupby("period"):
            key = str(period)
            symptom_counts = (group[list(SYMPTOM_FIELDS)] > 0).sum()
            top_key = symptom_counts.idxmax() if symptom_counts.sum() else None
            rows[key] = {
                "Period": key,
                "Check-ins": len(group),
                "Average daily impact": round(float(group["daily_impact"].mean()), 1),
                "Symptom events": 0,
                "Bleeding events": 0,
                "Medication changes": 0,
                "Most frequently selected symptom": SYMPTOM_FIELDS.get(top_key, "None recorded"),
            }

    if not events.empty:
        working = events.copy()
        working["period"] = working["event_date"].dt.to_period(period_code)
        for period, group in working.groupby("period"):
            key = str(period)
            row = rows.setdefault(key, {
                "Period": key,
                "Check-ins": 0,
                "Average daily impact": None,
                "Symptom events": 0,
                "Bleeding events": 0,
                "Medication changes": 0,
                "Most frequently selected symptom": "None recorded",
            })
            counts = group["event_type"].value_counts()
            row["Symptom events"] = int(counts.get("Symptom episode", 0))
            row["Bleeding events"] = int(counts.get("Bleeding", 0))
            row["Medication changes"] = int(counts.get("Medication change", 0))

    columns = [
        "Period", "Check-ins", "Average daily impact", "Symptom events",
        "Bleeding events", "Medication changes", "Most frequently selected symptom",
    ]
    return pd.DataFrame(sorted(rows.values(), key=lambda row: row["Period"]), columns=columns)


def filter_activity(
    check_ins: pd.DataFrame,
    events: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter both activity tables to an inclusive reporting date range."""
    if start_date > end_date:
        raise ValueError("Report start date must be on or before the end date.")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    filtered_check_ins = check_ins[
        check_ins["entry_date"].between(start, end, inclusive="both")
    ].copy() if not check_ins.empty else check_ins.copy()
    filtered_events = events[
        events["event_date"].between(start, end, inclusive="both")
    ].copy() if not events.empty else events.copy()
    return filtered_check_ins, filtered_events


def build_appointment_report(
    check_ins: pd.DataFrame,
    events: pd.DataFrame,
    start_date: date,
    end_date: date,
    questions_for_clinician: str = "",
) -> str:
    """Create a printable HTML summary of self-reported session activity."""
    check_ins, events = filter_activity(check_ins, events, start_date, end_date)
    summary = trend_summary(check_ins)
    event_counts = events["event_type"].value_counts() if not events.empty else pd.Series(dtype=int)
    frequency = "weekly" if (end_date - start_date).days <= 90 else "monthly"
    periods = period_summary(check_ins, events, frequency)

    def safe(value) -> str:
        if value is None or (not isinstance(value, str) and pd.isna(value)):
            return "-"
        return escape(str(value))

    period_rows = "".join(
        "<tr>" + "".join(f"<td>{safe(value)}</td>" for value in row) + "</tr>"
        for row in periods.itertuples(index=False, name=None)
    ) or "<tr><td colspan='7'>No activity in this date range.</td></tr>"

    event_rows = ""
    safety_rows = []
    for _, event in events.iterrows():
        event_rows += (
            "<tr>"
            f"<td>{event['event_date']:%Y-%m-%d}</td>"
            f"<td>{safe(event['event_type'])}</td>"
            f"<td>{safe(event['event_name'])}</td>"
            f"<td>{safe(event['severity'])}</td>"
            f"<td>{safe(event['change_type'])}</td>"
            f"<td>{safe(event['notes'])}</td>"
            "</tr>"
        )
        for notice in event_safety_notices(event.to_dict()):
            safety_rows.append(
                f"<li><strong>{event['event_date']:%Y-%m-%d}: {safe(notice['title'])}</strong> - {safe(notice['message'])}</li>"
            )
    if not event_rows:
        event_rows = "<tr><td colspan='6'>No specific events in this date range.</td></tr>"
    safety_html = "<ul>" + "".join(safety_rows) + "</ul>" if safety_rows else "<p>No built-in safety notice was triggered in the selected event logs. This does not establish medical safety.</p>"
    questions = safe(questions_for_clinician).replace("\n", "<br>") or "No questions entered."

    top_symptom = (
        f"{safe(summary['most_logged_symptom'])} ({summary['most_logged_symptom_mean']}/4 average logged intensity)"
        if summary["most_logged_symptom"] else "Unavailable"
    )
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>MenoCare appointment summary</title>
<style>
body{{font-family:Arial,sans-serif;color:#352b3a;max-width:1000px;margin:36px auto;padding:0 24px;line-height:1.45}}
h1,h2{{color:#97266d}} .notice{{background:#fff5f7;border-left:5px solid #d63384;padding:14px;margin:16px 0}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .metric{{border:1px solid #ead7e2;border-radius:10px;padding:12px}}
.metric strong{{display:block;font-size:1.35rem;color:#6f42c1}} table{{width:100%;border-collapse:collapse;margin:12px 0 24px}}
th,td{{border:1px solid #e2d8df;padding:8px;text-align:left;vertical-align:top}} th{{background:#faf5f8}}
.small{{color:#6b6570;font-size:.9rem}} @media print{{body{{margin:0;max-width:none}}}}
</style></head><body>
<h1>MenoCare appointment summary</h1>
<p class="small">Generated {generated}. Coverage: {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}.</p>
<div class="notice"><strong>Self-reported information</strong><br>This report summarizes entries from a session-only educational tracker. It is not a diagnosis, risk score, medical record, or treatment recommendation.</div>
<div class="metrics">
<div class="metric"><span>Quick check-ins</span><strong>{len(check_ins)}</strong></div>
<div class="metric"><span>Symptom events</span><strong>{int(event_counts.get('Symptom episode', 0))}</strong></div>
<div class="metric"><span>Bleeding events</span><strong>{int(event_counts.get('Bleeding', 0))}</strong></div>
<div class="metric"><span>Medication changes</span><strong>{int(event_counts.get('Medication change', 0))}</strong></div>
</div>
<p><strong>Highest average quick-check-in symptom:</strong> {top_symptom}</p>
<h2>{frequency.title()} overview</h2>
<table><thead><tr>{''.join(f'<th>{safe(column)}</th>' for column in periods.columns)}</tr></thead><tbody>{period_rows}</tbody></table>
<h2>Specific-event timeline</h2>
<table><thead><tr><th>Date</th><th>Type</th><th>Event</th><th>Severity</th><th>Change</th><th>Notes</th></tr></thead><tbody>{event_rows}</tbody></table>
<h2>Safety notices produced while logging</h2>{safety_html}
<h2>Questions for the clinician</h2><p>{questions}</p>
<div class="notice"><strong>Important:</strong> Absence of a safety notice does not mean symptoms are safe. Seek professional medical advice for concerning, persistent, severe, or worsening symptoms.</div>
</body></html>"""
