"""Regression checks for the session-only MenoCare tracker."""

import unittest
from datetime import date

from Dashboard.utils.menocare import (
    MENSTRUAL_STATUS_OPTIONS,
    SYMPTOM_FIELDS,
    build_appointment_report,
    create_bleeding_event,
    create_entry,
    create_medication_event,
    create_quick_check_in,
    create_symptom_event,
    entries_frame,
    events_frame,
    event_safety_notices,
    filter_activity,
    period_summary,
    safety_notices,
    trend_summary,
)


def sample_entry(**overrides):
    values = {
        "entry_date": date(2026, 11, 1),
        "menstrual_status": MENSTRUAL_STATUS_OPTIONS[0],
        "bleeding": "None",
        "symptoms": {field: 0 for field in SYMPTOM_FIELDS},
        "daily_impact": 0,
    }
    values.update(overrides)
    return create_entry(**values)


class MenoCareTests(unittest.TestCase):
    def test_quick_check_in_maps_only_selected_symptoms(self):
        entry = create_quick_check_in(
            entry_date=date(2026, 11, 3),
            selected_symptoms=["hot_flashes", "fatigue"],
            symptom_severity=3,
            daily_impact=2,
        )
        self.assertEqual(entry["hot_flashes"], 3)
        self.assertEqual(entry["fatigue"], 3)
        self.assertEqual(entry["night_sweats"], 0)
        self.assertEqual(entry["daily_impact"], 2)

    def test_quick_check_in_rejects_intensity_without_symptom(self):
        with self.assertRaisesRegex(ValueError, "Choose at least one"):
            create_quick_check_in(
                entry_date=date(2026, 11, 3),
                selected_symptoms=[],
                symptom_severity=2,
                daily_impact=1,
            )

    def test_quick_check_in_rejects_selected_symptom_with_zero_intensity(self):
        with self.assertRaisesRegex(ValueError, "at least Mild"):
            create_quick_check_in(
                entry_date=date(2026, 11, 3),
                selected_symptoms=["fatigue"],
                symptom_severity=0,
                daily_impact=1,
            )

    def test_normal_check_in_is_not_labelled_safe_or_diagnosed(self):
        entry = sample_entry()
        self.assertEqual(safety_notices(entry), [])
        self.assertNotIn("stage", entry)
        self.assertNotIn("diagnosis", entry)

    def test_postmenopausal_bleeding_prompts_assessment_even_for_spotting(self):
        entry = sample_entry(
            menstrual_status="No period for 12 months or more",
            bleeding="Spotting",
        )
        notices = safety_notices(entry)
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["level"], "prompt")
        self.assertIn("always be checked", notices[0]["message"])

    def test_heavy_bleeding_with_concerning_symptoms_is_emergency(self):
        entry = sample_entry(
            bleeding="Heavy",
            hourly_soaking_over_two_hours=True,
            concerning_bleeding_symptoms=True,
        )
        notices = safety_notices(entry)
        self.assertTrue(any(notice["level"] == "emergency" for notice in notices))

    def test_hourly_soaking_without_companion_symptoms_is_urgent(self):
        entry = sample_entry(hourly_soaking_over_two_hours=True)
        notices = safety_notices(entry)
        self.assertEqual(notices[0]["level"], "urgent")

    def test_severe_sudden_pain_is_emergency(self):
        entry = sample_entry(severe_sudden_pain=True)
        self.assertEqual(safety_notices(entry)[0]["level"], "emergency")

    def test_bleeding_event_uses_same_safety_rule(self):
        event = create_bleeding_event(
            event_date=date(2026, 11, 4),
            menstrual_status="No period for 12 months or more",
            bleeding="Spotting",
        )
        notices = event_safety_notices(event)
        self.assertEqual(notices[0]["level"], "prompt")

    def test_symptom_and_medication_events_are_normalized(self):
        symptom = create_symptom_event(
            event_date=date(2026, 11, 5), symptom="night_sweats",
            severity=2, duration_minutes=15,
        )
        medication = create_medication_event(
            event_date=date(2026, 11, 6), medication_name="Example medicine",
            change_type="Started",
        )
        frame = events_frame([medication, symptom])
        self.assertEqual(frame["event_type"].tolist(), ["Symptom episode", "Medication change"])
        self.assertEqual(frame.loc[0, "duration_minutes"], 15)
        self.assertEqual(frame.loc[1, "change_type"], "Started")

    def test_empty_medication_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "medication or supplement"):
            create_medication_event(
                event_date=date(2026, 11, 6), medication_name="  ",
                change_type="Started",
            )

    def test_weekly_and_monthly_summaries_count_activity(self):
        check_ins = entries_frame([
            create_quick_check_in(
                entry_date=date(2026, 11, 2), selected_symptoms=["fatigue"],
                symptom_severity=2, daily_impact=1,
            ),
            create_quick_check_in(
                entry_date=date(2026, 11, 10), selected_symptoms=["hot_flashes"],
                symptom_severity=3, daily_impact=2,
            ),
        ])
        events = events_frame([
            create_symptom_event(
                event_date=date(2026, 11, 3), symptom="night_sweats", severity=2,
            ),
            create_medication_event(
                event_date=date(2026, 11, 11), medication_name="Example medicine",
                change_type="Dose changed",
            ),
        ])
        weekly = period_summary(check_ins, events, "weekly")
        monthly = period_summary(check_ins, events, "monthly")
        self.assertEqual(int(weekly["Check-ins"].sum()), 2)
        self.assertEqual(int(weekly["Symptom events"].sum()), 1)
        self.assertEqual(int(weekly["Medication changes"].sum()), 1)
        self.assertEqual(len(monthly), 1)
        self.assertEqual(monthly.loc[0, "Period"], "2026-11")

    def test_report_filter_rejects_reversed_date_range(self):
        with self.assertRaisesRegex(ValueError, "start date"):
            filter_activity(
                entries_frame([]), events_frame([]),
                date(2026, 11, 5), date(2026, 11, 4),
            )

    def test_appointment_report_filters_and_escapes_sensitive_text(self):
        check_ins = entries_frame([
            create_quick_check_in(
                entry_date=date(2026, 11, 2), selected_symptoms=["fatigue"],
                symptom_severity=2, daily_impact=1,
                notes="<script>not safe</script>",
            )
        ])
        events = events_frame([
            create_bleeding_event(
                event_date=date(2026, 11, 3),
                menstrual_status="No period for 12 months or more",
                bleeding="Spotting", notes="Bring this up",
            ),
            create_medication_event(
                event_date=date(2026, 10, 1), medication_name="Outside range",
                change_type="Started",
            ),
        ])
        report = build_appointment_report(
            check_ins, events, date(2026, 11, 1), date(2026, 11, 30),
            "Could this be <b>related</b>?",
        )
        self.assertIn("MenoCare appointment summary", report)
        self.assertIn("Bleeding after 12 months", report)
        self.assertNotIn("Outside range", report)
        self.assertIn("&lt;b&gt;related&lt;/b&gt;", report)
        self.assertNotIn("<b>related</b>", report)

    def test_out_of_range_values_are_rejected(self):
        symptoms = {field: 0 for field in SYMPTOM_FIELDS}
        symptoms["hot_flashes"] = 5
        with self.assertRaisesRegex(ValueError, "Hot flashes"):
            sample_entry(symptoms=symptoms)
        with self.assertRaisesRegex(ValueError, "Daily impact"):
            sample_entry(daily_impact=-1)

    def test_entries_sort_and_summary_describe_logs_only(self):
        first_symptoms = {field: 0 for field in SYMPTOM_FIELDS}
        first_symptoms["hot_flashes"] = 4
        entries = [
            sample_entry(entry_date=date(2026, 11, 2)),
            sample_entry(entry_date=date(2026, 11, 1), symptoms=first_symptoms),
        ]
        frame = entries_frame(entries)
        summary = trend_summary(frame)
        self.assertEqual(frame.loc[0, "entry_date"].date(), date(2026, 11, 1))
        self.assertEqual(summary["entries"], 2)
        self.assertEqual(summary["days_logged"], 2)
        self.assertEqual(summary["most_logged_symptom"], "Hot flashes")
        self.assertEqual(summary["most_logged_symptom_mean"], 2.0)


if __name__ == "__main__":
    unittest.main()
