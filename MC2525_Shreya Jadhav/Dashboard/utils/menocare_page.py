"""Streamlit interface for the MenoCare session-only menopause tracker."""

from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from Dashboard.utils.menocare import (
    BLEEDING_OPTIONS,
    MEDICATION_CHANGE_OPTIONS,
    MENSTRUAL_STATUS_OPTIONS,
    SEVERITY_LABELS,
    SYMPTOM_FIELDS,
    build_appointment_report,
    create_bleeding_event,
    create_medication_event,
    create_quick_check_in,
    create_symptom_event,
    entries_frame,
    events_frame,
    event_safety_notices,
    filter_activity,
    period_summary,
    trend_summary,
)


PINK = "#D63384"
PURPLE = "#6F42C1"
TEAL = "#1F9D8A"
GOLD = "#F2B134"


def _severity_slider(label: str, key: str) -> int:
    return st.select_slider(
        label,
        options=list(SEVERITY_LABELS),
        value=0,
        format_func=lambda value: f"{value} · {SEVERITY_LABELS[value]}",
        key=key,
    )


def _show_notices(notices: list[dict[str, str]]) -> None:
    for notice in notices:
        text = f"**{notice['title']}**  \n{notice['message']}"
        if notice["level"] == "emergency":
            st.error(text)
        elif notice["level"] == "urgent":
            st.warning(text)
        else:
            st.warning(text)


def _render_check_in() -> None:
    st.subheader("Quick daily check-in")
    st.caption("A short reflection for trend tracking. Use Log an event when you want to record one specific episode in more detail.")

    with st.form("menocare_check_in", clear_on_submit=False):
        left, right = st.columns(2)
        with left:
            entry_date = st.date_input("Date", value=date.today(), max_value=date.today())
            selected_labels = st.multiselect(
                "What affected you today?",
                list(SYMPTOM_FIELDS.values()),
                placeholder="Choose any symptoms",
            )
        with right:
            daily_impact = _severity_slider("Overall impact on daily life", "meno_daily_impact")
            symptom_severity = _severity_slider("Overall symptom intensity", "meno_quick_severity")

        notes = st.text_area(
            "Optional short note",
            max_chars=1000,
            placeholder="What made today better or harder?",
        )
        submitted = st.form_submit_button("Save check-in", type="primary", width="stretch")

    if submitted:
        reverse_labels = {label: field for field, label in SYMPTOM_FIELDS.items()}
        try:
            entry = create_quick_check_in(
                entry_date=entry_date,
                selected_symptoms=[reverse_labels[label] for label in selected_labels],
                symptom_severity=symptom_severity,
                daily_impact=daily_impact,
                notes=notes,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state.setdefault("menocare_entries", []).append(entry)
            st.success("Quick check-in saved in this session.")


def _render_event_log() -> None:
    st.subheader("Log a specific event")
    st.caption("Use this when an episode or change matters on its own. Recording an event does not identify its cause.")
    event_type = st.radio(
        "What would you like to record?",
        ["Symptom episode", "Bleeding", "Medication change"],
        horizontal=True,
        key="meno_event_type",
    )

    if event_type == "Symptom episode":
        with st.form("meno_symptom_event"):
            left, right = st.columns(2)
            with left:
                event_date = st.date_input("Event date", value=date.today(), max_value=date.today(), key="meno_symptom_date")
                symptom_label = st.selectbox("Symptom", list(SYMPTOM_FIELDS.values()), key="meno_event_symptom")
            with right:
                severity = st.select_slider(
                    "Episode severity", options=[1, 2, 3, 4], value=2,
                    format_func=lambda value: f"{value} · {SEVERITY_LABELS[value]}",
                )
                duration = st.number_input("Approximate duration in minutes (optional)", min_value=0, max_value=1440, value=0)
            trigger = st.text_input("Possible trigger or context (optional)", max_chars=300)
            notes = st.text_area("Notes (optional)", max_chars=1000, key="meno_symptom_notes")
            submitted = st.form_submit_button("Save symptom event", type="primary", width="stretch")
        if submitted:
            symptom_key = {label: field for field, label in SYMPTOM_FIELDS.items()}[symptom_label]
            event = create_symptom_event(
                event_date=event_date,
                symptom=symptom_key,
                severity=severity,
                duration_minutes=duration or None,
                possible_trigger=trigger,
                notes=notes,
            )
            st.session_state.setdefault("menocare_events", []).append(event)
            st.success("Symptom event saved in this session.")

    elif event_type == "Bleeding":
        with st.form("meno_bleeding_event"):
            left, right = st.columns(2)
            with left:
                event_date = st.date_input("Event date", value=date.today(), max_value=date.today(), key="meno_bleeding_date")
                bleeding = st.selectbox("Bleeding type", BLEEDING_OPTIONS[1:], key="meno_event_bleeding")
            with right:
                menstrual_status = st.selectbox(
                    "Current menstrual situation", MENSTRUAL_STATUS_OPTIONS,
                    help="Self-reported context only; MenoCare does not determine menopause stage.",
                )
            hourly_soaking = st.checkbox("Soaking through a pad or tampon every hour for more than 2 hours", key="meno_event_hourly")
            concerning = st.checkbox("Chest pain, shortness of breath, faintness, or marked dizziness with the bleeding", key="meno_event_concerning")
            severe_pain = st.checkbox("Severe or sudden pelvic or abdominal pain", key="meno_event_pain")
            notes = st.text_area("Notes (optional)", max_chars=1000, key="meno_bleeding_notes")
            submitted = st.form_submit_button("Save bleeding event", type="primary", width="stretch")
        if submitted:
            event = create_bleeding_event(
                event_date=event_date,
                menstrual_status=menstrual_status,
                bleeding=bleeding,
                hourly_soaking_over_two_hours=hourly_soaking,
                concerning_bleeding_symptoms=concerning,
                severe_sudden_pain=severe_pain,
                notes=notes,
            )
            st.session_state.setdefault("menocare_events", []).append(event)
            st.success("Bleeding event saved in this session.")
            notices = event_safety_notices(event)
            _show_notices(notices)
            if not notices:
                st.info("No built-in red-flag rule was triggered. This does not confirm that the bleeding is medically safe; contact a clinician if you are concerned or the pattern is unusual for you.")

    else:
        with st.form("meno_medication_event"):
            left, right = st.columns(2)
            with left:
                event_date = st.date_input("Change date", value=date.today(), max_value=date.today(), key="meno_medication_date")
                medication = st.text_input("Medication or supplement name", max_chars=150)
            with right:
                change_type = st.selectbox("What changed?", MEDICATION_CHANGE_OPTIONS)
            notes = st.text_area(
                "Notes (optional)", max_chars=1000, key="meno_medication_notes",
                placeholder="For example: clinician instructions or why the change was recorded.",
            )
            submitted = st.form_submit_button("Save medication change", type="primary", width="stretch")
        if submitted:
            try:
                event = create_medication_event(
                    event_date=event_date,
                    medication_name=medication,
                    change_type=change_type,
                    notes=notes,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.setdefault("menocare_events", []).append(event)
                st.success("Medication change saved in this session. MenoCare has not assessed whether the change is appropriate.")


def _render_trends() -> None:
    st.subheader("Your session trends")
    frame = entries_frame(st.session_state.get("menocare_entries", []))
    event_frame = events_frame(st.session_state.get("menocare_events", []))
    if frame.empty and event_frame.empty:
        st.info("No activity yet. Add a quick check-in or log a specific event to begin your timeline.")
        return

    summary = trend_summary(frame)
    activity_dates = []
    if not frame.empty:
        activity_dates.append(frame["entry_date"].max())
    if not event_frame.empty:
        activity_dates.append(event_frame["event_date"].max())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Check-ins", summary["entries"])
    m2.metric("Specific events", len(event_frame))
    m3.metric("Latest activity", max(activity_dates).strftime("%d %b %Y"))
    m4.metric(
        "Highest average entry",
        f"{summary['most_logged_symptom']} ({summary['most_logged_symptom_mean']}/4)" if summary["most_logged_symptom"] else "Unavailable",
    )

    st.markdown("#### Weekly or monthly overview")
    st.session_state.setdefault(
        "meno_summary_frequency",
        st.session_state.get("menocare_summary_default", "Weekly"),
    )
    summary_frequency = st.radio(
        "Summary period", ["Weekly", "Monthly"], horizontal=True,
        key="meno_summary_frequency",
    )
    periods = period_summary(frame, event_frame, summary_frequency.lower())
    if not periods.empty:
        count_columns = ["Check-ins", "Symptom events", "Bleeding events", "Medication changes"]
        period_chart = periods.melt(
            id_vars="Period", value_vars=count_columns,
            var_name="Activity", value_name="Count",
        )
        fig_period = px.bar(
            period_chart, x="Period", y="Count", color="Activity", barmode="group",
            color_discrete_sequence=[PINK, PURPLE, TEAL, GOLD],
        )
        fig_period.update_layout(
            height=360, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", legend_title_text="",
        )
        st.plotly_chart(fig_period, width="stretch", config={"displayModeBar": False})
        st.dataframe(periods, hide_index=True, width="stretch")

    if not frame.empty:
        chart_data = frame[["entry_date", *SYMPTOM_FIELDS.keys()]].melt(
            id_vars="entry_date", var_name="symptom", value_name="severity"
        )
        chart_data["symptom"] = chart_data["symptom"].map(SYMPTOM_FIELDS)
        selected = st.multiselect(
            "Symptoms to compare",
            list(SYMPTOM_FIELDS.values()),
            default=list(SYMPTOM_FIELDS.values())[:4],
        )
        if selected:
            fig = px.line(
                chart_data[chart_data["symptom"].isin(selected)],
                x="entry_date", y="severity", color="symptom", markers=True,
                color_discrete_sequence=[PINK, PURPLE, TEAL, GOLD, "#F05D7B", "#4776E6"],
                labels={"entry_date": "Date", "severity": "Self-reported intensity", "symptom": "Symptom"},
            )
            fig.update_yaxes(range=[0, 4], tickvals=list(SEVERITY_LABELS), ticktext=list(SEVERITY_LABELS.values()))
            fig.update_layout(height=430, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        st.caption("The quick-check-in chart uses one overall intensity for the symptoms selected that day. Log a specific event when separate severity or duration matters.")
        display = frame.copy()
        display["entry_date"] = display["entry_date"].dt.strftime("%Y-%m-%d")
        display = display.rename(columns={**SYMPTOM_FIELDS, "entry_date": "Date", "daily_impact": "Daily impact"})
        with st.expander("Quick check-in history"):
            st.dataframe(display[["Date", *SYMPTOM_FIELDS.values(), "Daily impact", "notes"]], hide_index=True, width="stretch")

    if not event_frame.empty:
        st.markdown("#### Specific-event timeline")
        event_display = event_frame.copy()
        event_display["event_date"] = event_display["event_date"].dt.strftime("%Y-%m-%d")
        event_display = event_display.rename(columns={
            "event_date": "Date", "event_type": "Type", "event_name": "Event",
            "severity": "Severity", "duration_minutes": "Minutes",
            "change_type": "Change", "notes": "Notes",
        })
        st.dataframe(event_display[["Date", "Type", "Event", "Severity", "Minutes", "Change", "Notes"]], hide_index=True, width="stretch")

    export_left, export_right = st.columns(2)
    with export_left:
        st.download_button(
            "Download quick check-ins",
            data=frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="menocare_quick_checkins.csv",
            mime="text/csv",
            disabled=frame.empty,
            width="stretch",
        )
    with export_right:
        st.download_button(
            "Download event timeline",
            data=event_frame.to_csv(index=False).encode("utf-8-sig"),
            file_name="menocare_events.csv",
            mime="text/csv",
            disabled=event_frame.empty,
            width="stretch",
        )


def _render_report() -> None:
    st.subheader("Appointment report")
    st.caption("Choose a date range and download a printable summary to discuss with a healthcare professional.")
    frame = entries_frame(st.session_state.get("menocare_entries", []))
    event_frame = events_frame(st.session_state.get("menocare_events", []))
    if frame.empty and event_frame.empty:
        st.info("Add at least one quick check-in or event before creating a report.")
        return

    available_dates = []
    if not frame.empty:
        available_dates.extend(frame["entry_date"].dt.date.tolist())
    if not event_frame.empty:
        available_dates.extend(event_frame["event_date"].dt.date.tolist())
    earliest, latest = min(available_dates), max(available_dates)

    left, right = st.columns(2)
    with left:
        report_start = st.date_input(
            "Report starts", value=earliest, min_value=earliest, max_value=latest,
            key="meno_report_start",
        )
    with right:
        report_end = st.date_input(
            "Report ends", value=latest, min_value=earliest, max_value=latest,
            key="meno_report_end",
        )
    questions = st.text_area(
        "Questions to take to the appointment (optional)",
        max_chars=2000,
        placeholder="For example: Could these sleep changes be related to menopause? What treatment options fit my medical history?",
        key="meno_clinician_questions",
    )

    try:
        report_check_ins, report_events = filter_activity(
            frame, event_frame, report_start, report_end
        )
        report_html = build_appointment_report(
            frame, event_frame, report_start, report_end, questions
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    event_counts = report_events["event_type"].value_counts() if not report_events.empty else {}
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Included check-ins", len(report_check_ins))
    p2.metric("Symptom events", int(event_counts.get("Symptom episode", 0)))
    p3.metric("Bleeding events", int(event_counts.get("Bleeding", 0)))
    p4.metric("Medication changes", int(event_counts.get("Medication change", 0)))
    st.info(
        "The downloaded file opens in a web browser and can be printed or saved as PDF. "
        "Review it before sharing because it may contain sensitive notes and medication information."
    )
    st.download_button(
        "Download printable appointment report",
        data=report_html.encode("utf-8"),
        file_name=f"menocare_appointment_summary_{report_start}_{report_end}.html",
        mime="text/html",
        width="stretch",
    )


def _render_learn() -> None:
    st.subheader("Understand the transition")
    st.markdown(
        """
        **Perimenopause** is the time leading up to menopause. Periods may become shorter, longer, lighter,
        heavier, or may be skipped. Hot flashes, night sweats, sleep problems, mood changes, concentration
        difficulty, vaginal dryness, and urinary symptoms can occur, but experiences vary widely.

        **Menopause** is defined retrospectively after 12 consecutive months without a period when there is
        no other explanation. An app cannot confirm the cause of symptoms or safely choose treatment.
        """
    )
    st.markdown("#### When to seek medical help")
    st.markdown(
        """
        - Arrange a medical assessment for any bleeding after 12 months without a period, even if it is light or happens once.
        - Discuss bleeding between periods, after sex, or bleeding that is unusually heavy or prolonged with a clinician.
        - Seek emergency care for very heavy bleeding accompanied by chest pain, shortness of breath, faintness, or marked dizziness.
        - Seek urgent assessment for severe or sudden pelvic or abdominal pain.
        """
    )
    st.markdown(
        "Trusted references: [ACOG - The Menopause Years](https://www.acog.org/womens-health/faqs/the-menopause-years) · "
        "[ACOG - Abnormal Uterine Bleeding](https://www.acog.org/womens-health/faqs/abnormal-uterine-bleeding) · "
        "[NHS - Postmenopausal Bleeding](https://www.nhs.uk/symptoms/post-menopausal-bleeding/) · "
        "[SWAN Data Access](https://www.swanstudy.org/swan-research/data-access/)"
    )


def render_menocare() -> None:
    """Render the MenoCare MVP without persistent storage or diagnosis."""
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">🌙 MenoCare</div>
            <p class="hero-subtitle">Track menopause-transition symptoms, bleeding changes, and daily impact.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Privacy for this MVP: entries stay only in the current Streamlit session and disappear when the session resets. "
        "There is no account, cloud storage, or clinician monitoring."
    )
    st.warning("MenoCare is an educational tracker, not a diagnostic or treatment tool. It cannot determine whether you are in perimenopause or menopause.")

    check_in, events, trends, report, learn = st.tabs(["⚡ Quick check-in", "➕ Log an event", "📈 Trends", "📄 Appointment report", "📚 Learn & safety"])
    with check_in:
        _render_check_in()
    with events:
        _render_event_log()
    with trends:
        _render_trends()
    with report:
        _render_report()
    with learn:
        _render_learn()
