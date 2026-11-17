import json
import urllib.request
import urllib.error


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "llama3.2:latest"


# ============================================================
# GENERATE LLAMA EXPLANATION
# ============================================================

def generate_explanation(
    claim,
    verdict,
    ml_prediction,
    ml_confidence,
    evidence_score,
    evidence_status
):
    """
    Llama is ONLY an explanation layer.

    It does NOT:
        - verify the claim
        - perform web searches
        - change the verdict
        - invent evidence
        - introduce new facts

    The actual verdict comes from:
        ML Model
        Evidence Matcher
        Fusion Engine
    """


    prompt = f"""
You are an explanation component inside a multilingual
news verification system.

Your job is ONLY to explain the verification result
already calculated by the system.

IMPORTANT RULES:

1. Do NOT change the SYSTEM VERDICT.

2. Do NOT independently decide whether the claim is true
   or false.

3. Do NOT perform a web search.

4. Do NOT invent facts.

5. Do NOT mention facts that are not present in the
   verification information below.

6. Do NOT claim that an article proves the claim unless
   the supplied evidence status says Supporting Evidence
   or Strong Supporting Evidence.

7. If the evidence status is:
   "No Evidence"
   or
   "Related but not conclusive"
   explain that the available evidence is insufficient
   for a definitive conclusion.

8. If the verdict is "Needs Verification", clearly say
   that the available information is not sufficient to
   establish the claim as true or false.

9. Keep the explanation concise.

10. Return ONLY the explanation.

VERIFICATION INFORMATION
=========================

CLAIM:
{claim}

SYSTEM VERDICT:
{verdict}

ML PREDICTION:
{ml_prediction}

ML CONFIDENCE:
{ml_confidence}%

EVIDENCE SCORE:
{evidence_score}%

EVIDENCE STATUS:
{evidence_status}

Write 2 to 4 short professional sentences.

The explanation must:
- state the system verdict;
- briefly explain the ML contribution;
- explain what the evidence status/score indicates;
- avoid adding unsupported facts.
"""


    # ========================================================
    # OLLAMA REQUEST
    # ========================================================

    payload = {

        "model":
            MODEL_NAME,

        "prompt":
            prompt,

        "stream":
            False,

        "options": {

            "temperature":
                0.0,

            "num_predict":
                180

        }

    }


    try:

        request_data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )


        request = urllib.request.Request(

            OLLAMA_URL,

            data=request_data,

            headers={
                "Content-Type":
                    "application/json"
            },

            method="POST"

        )


        with urllib.request.urlopen(

            request,

            timeout=120

        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )


        result = json.loads(
            response_data
        )


        explanation = str(
            result.get(
                "response",
                ""
            )
        ).strip()


        if not explanation:

            return (
                "Llama did not return an explanation."
            )


        # ----------------------------------------------------
        # Remove accidental markdown wrappers.
        # ----------------------------------------------------

        explanation = (
            explanation
            .replace(
                "Explanation:",
                ""
            )
            .strip()
        )


        return explanation


    except urllib.error.URLError as error:

        print(
            "\nLlama/Ollama connection error:"
        )

        print(
            str(error)
        )

        return (
            "Llama explanation is currently unavailable."
        )


    except TimeoutError:

        print(
            "\nLlama request timed out."
        )

        return (
            "Llama explanation is currently unavailable."
        )


    except Exception as error:

        print(
            "\nLlama error:"
        )

        print(
            str(error)
        )

        return (
            "Llama explanation is currently unavailable."
        )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        " LLAMA 3.2 NEWS VERIFICATION TEST"
    )

    print(
        "========================================"
    )


    test_claim = (
        "India beat Sri Lanka by 165 runs "
        "in the first Test in Galle."
    )


    print(
        "\nSending verification result to Llama..."
    )


    explanation = generate_explanation(

        claim=test_claim,

        verdict="Likely Real",

        ml_prediction="Real",

        ml_confidence=55.28,

        evidence_score=99.73,

        evidence_status=
            "Strong Supporting Evidence"

    )


    print(
        "\n========================================"
    )

    print(
        " LLAMA EXPLANATION"
    )

    print(
        "========================================"
    )


    print(
        explanation
    )


    print(
        "\n========================================"
    )

    print(
        " TEST COMPLETED"
    )

    print(
        "========================================"
    )