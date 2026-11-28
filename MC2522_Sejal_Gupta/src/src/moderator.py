import os
import requests

from dotenv import load_dotenv
from utils.preprocess import preprocess_text


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(override=True)

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is missing. Add your Hugging Face token to .env"
    )


# ============================================================
# HUGGING FACE CONFIGURATION
# ============================================================

HF_MODEL = (
    "MoritzLaurer/"
    "mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
)

HF_API_URL = (
    f"https://router.huggingface.co/"
    f"hf-inference/models/{HF_MODEL}"
)


# ============================================================
# MODERATION FUNCTION
# ============================================================

def analyze_comment(comment):

    if not comment or not comment.strip():
        raise ValueError("Comment cannot be empty.")

    # Clean text
    clean_comment = preprocess_text(comment)

    # --------------------------------------------------------
    # Moderation categories
    # --------------------------------------------------------

    candidate_labels = [
        "toxic or abusive language",
        "non-toxic respectful language",
        "insult",
        "threat",
        "obscene language",
        "identity hate"
    ]

    # --------------------------------------------------------
    # Request payload
    # --------------------------------------------------------

    payload = {
        "inputs": clean_comment,
        "parameters": {
            "candidate_labels": candidate_labels,
            "multi_label": False,
            "hypothesis_template": (
                "This social media comment contains {}."
            )
        }
    }

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    try:

        # ====================================================
        # HUGGING FACE API CALL
        # ====================================================

        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        # Raise error for 4xx / 5xx
        response.raise_for_status()

        data = response.json()

        # ====================================================
        # DEBUG SAFETY
        # ====================================================

        if not isinstance(data, list):
            raise RuntimeError(
                f"Unexpected Hugging Face response: {data}"
            )

        if len(data) == 0:
            raise RuntimeError(
                "Hugging Face returned an empty result."
            )

        # ====================================================
        # NORMALIZE RESPONSE
        # ====================================================

        results = []

        for item in data:

            if isinstance(item, dict):

                label = item.get("label")
                score = item.get("score")

                if label is not None and score is not None:

                    results.append({
                        "label": str(label),
                        "score": float(score)
                    })

        if not results:
            raise RuntimeError(
                f"Invalid Hugging Face response: {data}"
            )

        # Highest confidence first
        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # ====================================================
        # TOP PREDICTION
        # ====================================================

        top_result = results[0]

        top_label = top_result["label"]
        top_score = top_result["score"]

        lower_label = top_label.lower()

        # ====================================================
        # DETERMINE TOXICITY
        # ====================================================

        toxic_labels = [
            "toxic or abusive language",
            "insult",
            "threat",
            "obscene language",
            "identity hate"
        ]

        is_toxic = any(
            label in lower_label
            for label in toxic_labels
        )

        # Explicitly protect the non-toxic class
        if "non-toxic" in lower_label:
            is_toxic = False

        # ====================================================
        # CATEGORY
        # ====================================================

        if "threat" in lower_label:

            category = "Threat"

        elif "obscene" in lower_label:

            category = "Obscene Language"

        elif "identity" in lower_label:

            category = "Identity Hate"

        elif "insult" in lower_label:

            category = "Insult"

        elif "toxic" in lower_label:

            category = "Offensive Language"

        else:

            category = "Safe"

        # ====================================================
        # SEVERITY
        # ====================================================

        if not is_toxic:

            severity = "Low"

        elif top_score >= 0.85:

            severity = "High"

        elif top_score >= 0.60:

            severity = "Medium"

        else:

            severity = "Low"

        # ====================================================
        # FINAL REPORT
        # ====================================================

        if is_toxic:

            return f"""
🚨 **Toxic Comment**

**Category:** {category}

**Severity:** {severity}

**Confidence:** {top_score * 100:.2f}%

**Explanation:**
Hugging Face detected potentially harmful or abusive
language in this social media comment.

**Suggested Polite Version:**
Please communicate respectfully and avoid offensive language.

**Hugging Face Prediction:**
{top_label}
"""

        else:

            return f"""
✅ **Non-Toxic Comment**

**Category:** Safe

**Severity:** Low

**Confidence:** {top_score * 100:.2f}%

**Explanation:**
Hugging Face did not identify significant harmful
language in this social media comment.

**Suggested Polite Version:**
No changes required.

**Hugging Face Prediction:**
{top_label}
"""

    except requests.exceptions.HTTPError as e:

        # Give a clean API error
        try:
            error_details = response.json()
        except Exception:
            error_details = response.text

        raise RuntimeError(
            f"Hugging Face API error "
            f"{response.status_code}: {error_details}"
        ) from e

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Could not connect to Hugging Face API: {e}"
        ) from e

    except Exception as e:

        raise RuntimeError(
            f"Hugging Face processing failed: {e}"
        ) from e