import json
import urllib.request

try:
    import ollama
except ImportError:
    ollama = None

MODEL = "llama3.2:3b"


def ask_llm(question, context="", clinical_report="", mode="knowledge"):

    if not context.strip():
        return (
            "I couldn't find a reliable source for that in the current medical "
            "knowledge base. I can't assess or diagnose symptoms from this chat; "
            "please ask a healthcare professional if they concern you."
        )

    if mode == "clinical":

        system_prompt = f"""
You are FemCare AI, an educational menstrual-health assistant, not a clinician.
Do not diagnose, assign a numeric risk, or claim to rule out an urgent condition.
The symptom summary is only what the user reported; its missing fields are unknown,
not evidence that the user has no concerning symptoms. Use only the supporting
medical knowledge for medical claims. Do not speculate about possible causes
unless the retrieved source explicitly supports them. Answer every part of the
question directly; if the source does not cover a part, say so. Recommend a
healthcare professional for persistent, worsening, or concerning symptoms.

Reported Symptom Summary
--------------------
{clinical_report}

Supporting Medical Knowledge
----------------------------
{context}

User Question
-------------
{question}

Give a short, plain-language response. Do not present a diagnosis or a
speculative differential. Briefly cite relevant source names or links.
"""

    else:

        system_prompt = f"""
You are FemCare AI, an educational menstrual-health assistant.

Use only the retrieved material below for medical claims. Answer the user's
actual question directly in plain language, preferably in two to four short
paragraphs or bullets. Answer every part of a multi-part question. For a
comparison, explain how the terms relate before listing any differences
supported by the material.

If the material supports only part of the answer, give that part and clearly
say what the sources do not establish. Do not invent a distinction, diagnosis,
treatment, or statistic. Do not treat individual records or state-level figures
as evidence about a person's diagnosis. If the material does not support any
answer, say:

"I couldn't find enough information in the available medical knowledge."

When references are included in the material, mention the relevant source
names or links briefly. Do not invent a source or cite an unrelated passage.
Suggest professional evaluation only when relevant to the question or symptoms.

Retrieved Medical Knowledge
---------------------------
{context}

Question
--------
{question}

Write a concise answer suitable for a patient.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    if ollama is not None:
        response = ollama.chat(model=MODEL, messages=messages)
        return response["message"]["content"]

    payload = json.dumps(
        {"model": MODEL, "messages": messages, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["message"]["content"]
