"""Conservative red-flag checks for self-reported symptoms.

This is a safety gate, not a diagnostic or validated clinical scoring tool.
References: https://www.nhs.uk/symptoms/pelvic-pain/ and
https://www.acog.org/womens-health/faqs/heavy-menstrual-bleeding
"""

from __future__ import annotations

import re


def assess_urgency(text: str, pain_score: int | None = None) -> dict:
    q = text.lower()
    # Handle common explicit negations before looking for safety words. This is
    # intentionally narrow; ambiguous wording should not suppress a warning.
    q = re.sub(
        r"\b(?:no|without|not having|don't have|do not have)\s+(?:any\s+)?"
        r"(?:severe\s+|sudden\s+)?(?:pelvic\s+|lower abdominal\s+|abdominal\s+)?pain\b",
        "",
        q,
    )
    q = re.sub(r"\b(?:no|without|not having|don't have|do not have)\s+fever\b", "", q)
    q = re.sub(
        r"\b(?:not|never)\s+(?:soaking|bleeding through|changing)\b.{0,45}"
        r"\b(?:pad|tampon)s?\b.{0,30}\b(?:every|an?|per)\s+hour\b",
        "",
        q,
    )
    pelvic_pain = bool(re.search(
        r"\b(?:pelvic|lower abdominal|abdominal|tummy|stomach)\s+pain\b|"
        r"\bpain\s+(?:in|around)\s+(?:my\s+)?(?:pelvis|lower abdomen)\b",
        q,
    ))
    severe_pain = bool(
        (pain_score is not None and pain_score >= 7)
        or re.search(r"\b(?:severe|sudden|intense|unbearable|worsening)\b.{0,45}\bpain\b", q)
        or re.search(r"\bpain\b.{0,45}\b(?:severe|unbearable|getting worse)\b", q)
    )
    hourly_pad = bool(re.search(
        r"\b(?:soak(?:ing|ed|s)?|bleed(?:ing)?\s+through|chang(?:e|ing))\b"
        r".{0,55}\b(?:pad|tampon)s?\b.{0,45}\b(?:every|an?|per)\s+hour\b",
        q,
    ))
    faint = bool(re.search(r"\b(?:faint(?:ed|ing)?|pass(?:ed|ing)? out|lightheaded)\b", q))
    fever = bool(re.search(r"\b(?:fever|high temperature|shivering)\b", q))
    possible_pregnancy = bool(re.search(
        r"\b(?:missed (?:a |my )?period|period is late|might be pregnant|may be pregnant|"
        r"could be pregnant|positive pregnancy test)\b", q
    ))

    reasons = []
    level = "none"
    if pelvic_pain and severe_pain:
        reasons.append("severe pelvic or abdominal pain")
        level = "emergency"
    if severe_pain and hourly_pad:
        reasons.append("severe pain together with rapid bleeding")
        level = "emergency"
    if pelvic_pain and faint:
        reasons.append("pelvic pain with faintness")
        level = "emergency"
    if hourly_pad:
        reasons.append("soaking or changing a pad or tampon about every hour")
        if level != "emergency":
            level = "prompt"
    if pelvic_pain and (fever or possible_pregnancy):
        reasons.append("pelvic pain with fever or a possible pregnancy")
        if level != "emergency":
            level = "prompt"
    if severe_pain and level == "none":
        reasons.append("severe pain")
        level = "prompt"
    return {"level": level, "reasons": list(dict.fromkeys(reasons))}


def safety_response(result: dict) -> str | None:
    level = result["level"]
    if level == "none":
        return None
    reasons = ", ".join(result["reasons"])
    has_pelvic_pain = any("pelvic" in reason for reason in result["reasons"])
    if level == "emergency":
        action = (
            "**Please seek emergency medical care now.** These symptoms can need "
            "immediate assessment. Do not wait for this chatbot or "
            "rely on home remedies. If you might be pregnant, tell the care team."
        )
    else:
        action = (
            "**Please seek prompt medical advice today** (an urgent-care service or "
            "your clinician). If pain becomes severe, you feel faint, or bleeding "
            "worsens, seek emergency care."
        )
    source_links = []
    if has_pelvic_pain:
        source_links.append("[NHS pelvic-pain guidance](https://www.nhs.uk/symptoms/pelvic-pain/)")
    if any("pad or tampon" in reason or "rapid bleeding" in reason for reason in result["reasons"]):
        source_links.append(
            "[ACOG heavy-bleeding guidance](https://www.acog.org/womens-health/faqs/heavy-menstrual-bleeding)"
        )
    if not source_links:
        source_links.append("[NHS period-pain guidance](https://www.nhs.uk/symptoms/period-pain/)")
    return (
        f"You reported {reasons}. {action}\n\n"
        "I cannot determine the cause or diagnose it from a chat. "
        f"Sources: {', '.join(source_links)}."
    )
