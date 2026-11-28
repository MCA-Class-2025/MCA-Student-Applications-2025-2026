import re

from Dashboard.utils.clinical_safety import assess_urgency, safety_response


# -----------------------------
# Extraction Functions
# -----------------------------

def extract_number(text, keywords):

    text = text.lower()

    for keyword in keywords:

        patterns = [

            rf"{keyword}\s*(?:level)?\s*(?:is|=|:)?\s*(\d+)",

            rf"{keyword}\s*(\d+)/10",

            rf"{keyword}\D*(\d+)",

            rf"(\d+)/10\s*{keyword}",

        ]

        for pattern in patterns:

            match = re.search(pattern, text)

            if match:
                value = int(match.group(1))

                if 0 <= value <= 10:
                    return value

    return None


def extract_sleep(text):

    patterns = [

        r"slept\s*(\d+)",

        r"sleep(?:ing)?(?:\s*hours?)?\s*(?:is|=|:)?\s*(\d+)",

        r"(\d+)\s*hours?\s*of\s*sleep",

        r"sleep\s*(\d+)"

    ]

    for pattern in patterns:

        match = re.search(pattern, text.lower())

        if match:

            return int(match.group(1))

    return None


def extract_flow(text):

    t = text.lower()

    for label in ("heavy", "moderate", "light"):
        if re.search(
            rf"\b{label}\s+(?:menstrual\s+)?(?:flow|bleeding|period)\b|"
            rf"\b(?:flow|bleeding|period)\s*(?:is|was|:|=)?\s*{label}\b",
            t,
        ):
            return label.title()

    return None


def extract_pcos(text):

    t = text.lower()

    # A question about possibly having PCOS is not a reported diagnosis.
    if re.search(
        r"\b(?:can|could|do|did|might|may|would|should|if)\s+i\s+have\s+pcos\b|"
        r"\bis it possible (?:that )?i have pcos\b",
        t,
    ):
        return False

    phrases = [

        "i have pcos",

        "diagnosed with pcos",

        "pcos yes",

        "pcos: yes",

        "pcos = yes"

    ]

    return any(p in t for p in phrases)


# -----------------------------
# Clinical Engine
# -----------------------------

def analyze(text):

    pain = extract_number(text, ["pain"])

    stress = extract_number(text, ["stress"])

    sleep = extract_sleep(text)

    flow = extract_flow(text)

    has_pcos = extract_pcos(text)

    safety = assess_urgency(text, pain)

    findings = []

    recommendations = []

    pain_status = None
    stress_status = None
    sleep_status = None

    # ---------------- Pain ----------------

    if pain is not None:

        if pain <= 3:
            pain_status = "🟢 Mild"

        elif pain <= 6:
            pain_status = "🟡 Moderate"

        else:
            pain_status = "🔴 Severe"
            findings.append("Severe pain reported.")
            recommendations.append("Severe or persistent pain should be evaluated by a clinician.")

    # ---------------- Stress ----------------

    if stress is not None:

        if stress <= 3:
            stress_status = "🟢 Low"

        elif stress <= 6:
            stress_status = "🟡 Moderate"

        else:
            stress_status = "🔴 High"
            findings.append("High stress may worsen menstrual symptoms.")
            recommendations.append("Stress management techniques may help reduce symptom severity.")

    # ---------------- Sleep ----------------

    if sleep is not None:

        if sleep < 6:
            sleep_status = "🔴 Inadequate"
            findings.append("Insufficient sleep may increase pain perception.")
            recommendations.append("Aim for 7–9 hours of sleep.")

        else:
            sleep_status = "🟢 Adequate"

    # ---------------- Flow ----------------

    if flow == "Heavy":

        findings.append("Heavy menstrual flow reported.")

        recommendations.append("Monitor heavy bleeding and seek medical advice if persistent.")

    # ---------------- PCOS ----------------

    if has_pcos:

        findings.append("History of PCOS reported.")

        recommendations.append("Continue regular follow-up for PCOS management.")

    if re.search(
        r"\b(?:missed (?:a |my )?period|periods? (?:have )?stopped|"
        r"no period for|periods? (?:have )?not come)\b",
        text,
        re.IGNORECASE,
    ):
        findings.append("A missed or stopped period was reported.")
        recommendations.append("Discuss a missed or stopped period with a clinician.")

    # ---------------- Risk ----------------

    if safety["level"] == "emergency":
        risk = "🔴 Seek emergency care"
    elif safety["level"] == "prompt":
        risk = "🟠 Prompt medical review"
    elif findings:
        risk = "ℹ️ Review symptoms with a clinician"
    else:
        risk = "⚪ Assessment limited by reported details"

    for reason in safety["reasons"]:
        findings.append(f"Safety flag: {reason}.")
    if safety["level"] != "none":
        recommendations.insert(0, "Follow the urgent-care advice in the response above.")

    # ---------------- Clinical Report ----------------

    report = f"""
Reported Symptom Summary (not a diagnosis)

Pain: {pain_status or "Not Provided"}

Stress: {stress_status or "Not Provided"}

Sleep: {sleep_status or "Not Provided"}

Flow: {flow or "Not Provided"}

PCOS: {"Reported by user" if has_pcos else "Not reported"}

Safety check (not a diagnosis): {risk}

Key Findings:
{chr(10).join("- " + x for x in findings) if findings else "- Details are insufficient to assess symptoms; this is not a diagnosis."}

Recommendations:
{chr(10).join("- " + x for x in recommendations) if recommendations else "- Ask a clinician if symptoms persist or concern you."}
"""

    return {

        "report": report,

        "pain": pain_status,

        "stress": stress_status,

        "sleep": sleep_status,

        "flow": flow,

        "pcos": has_pcos,

        "risk": risk,

        "findings": findings,

        "recommendations": recommendations,

        "urgency": safety["level"],

        "urgent_answer": safety_response(safety),

    }
