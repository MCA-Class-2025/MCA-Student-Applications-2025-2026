"""Source-backed answers for terminology questions the small local model misstates."""

from __future__ import annotations

import re


def curated_medical_answer(question: str, documents: list[dict]) -> str | None:
    """Return a fixed answer only when its supporting knowledge was retrieved."""

    if not (
        re.search(r"\bpcos\b", question, re.IGNORECASE)
        and re.search(r"\bpcod\b", question, re.IGNORECASE)
        and any(doc.get("source") == "pcos_pcod_terms.txt" for doc in documents)
    ):
        return None

    # This short fixed answer covers terminology and fertility only. Let the
    # sourced model handle other compound questions instead of dropping a part.
    if re.search(
        r"\b(?:treat(?:ment)?|cure|medication|medicine|diet|exercise|"
        r"symptoms?|risk factors?)\b",
        question,
        re.IGNORECASE,
    ):
        return None

    fertility_answer = ""
    if re.search(r"\b(?:fertility|infertil(?:e|ity)|pregnan\w*|conceiv\w*)\b", question, re.IGNORECASE):
        fertility_answer = (
            "\n\n**It can affect fertility**, because ovulation may be irregular, "
            "but infertility is not inevitable and treatments can help people "
            "who want to conceive. "
            "[WHO describes these effects and options](https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome)."
        )

    return (
        "**PCOD and PCOS are usually names for the same condition, not two "
        "separate diagnoses.** PCOD means *polycystic ovarian disease* and is "
        "an older name. PCOS means *polycystic ovary syndrome*. The "
        "[international guideline](https://www.monash.edu/medicine/mchri/pcos/guideline) "
        "adopted the name PMOS (*polyendocrine metabolic ovarian syndrome*) "
        "in 2026.\n\n"
        "The important question is what findings a clinician used. An ultrasound "
        "showing polycystic ovaries alone does not establish the syndrome, and "
        "a person can have it without that ultrasound appearance. "
        "[WHO explains the diagnostic approach](https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome). "
        "If a report says PCOD, ask the clinician what they meant and how the "
        "diagnosis was made."
        + fertility_answer
    )
