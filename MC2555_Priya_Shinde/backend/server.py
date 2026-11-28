import sys
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_DIR = PROJECT_ROOT / "backend" / "api"
FUSION_DIR = PROJECT_ROOT / "backend" / "fusion"
ML_DIR = PROJECT_ROOT / "backend" / "ml"


# ============================================================
# PYTHON IMPORT PATH
# ============================================================

for directory in [API_DIR, FUSION_DIR, ML_DIR]:

    directory_string = str(directory)

    if directory_string not in sys.path:
        sys.path.insert(0, directory_string)


# ============================================================
# IMPORT EXISTING VERIFICATION PIPELINE
# ============================================================
#
# We are using your existing verify_news.py.
# Nothing inside the ML/API/evidence pipeline is duplicated here.
#
# verify_news(claim) returns:
# {
#     "claim": ...,
#     "language": ...,
#     "ml_prediction": ...,
#     "ml_confidence": ...,
#     "articles_found": ...,
#     "evidence": [...],
#     "fusion_evidence": [...],
#     "fusion": {...}
# }
#
# ============================================================

from verify_news import verify_news


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

CORS(app)


# ============================================================
# JSON SERIALIZATION HELPER
# ============================================================

def make_json_safe(value):
    """
    Convert common Python / NumPy values into JSON-safe values.

    This prevents errors when the ML/evidence modules return
    NumPy numeric types or other non-standard values.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (str, int, float)):
        return value

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    # NumPy values and similar scalar objects
    if hasattr(value, "item"):

        try:
            return value.item()

        except Exception:
            pass

    # Fallback: convert unknown objects to strings
    return str(value)


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "success": True,

        "message":
            "Multilingual News Verification API is running",

        "status":
            "online"

    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "success": True,

        "service":
            "Multilingual News Verification",

        "status":
            "healthy"

    })


# ============================================================
# VERIFY NEWS
# ============================================================

@app.route("/api/verify", methods=["POST"])
def verify():

    try:

        # ----------------------------------------------------
        # READ REQUEST
        # ----------------------------------------------------

        data = request.get_json(silent=True)

        if not data:

            return jsonify({

                "success": False,

                "error":
                    "Request body must contain JSON data."

            }), 400


        # ----------------------------------------------------
        # GET CLAIM
        # ----------------------------------------------------

        claim = data.get(
            "claim",
            ""
        )


        if not isinstance(claim, str):

            return jsonify({

                "success": False,

                "error":
                    "Claim must be a string."

            }), 400


        claim = claim.strip()


        # ----------------------------------------------------
        # EMPTY CLAIM
        # ----------------------------------------------------

        if not claim:

            return jsonify({

                "success": False,

                "error":
                    "News claim cannot be empty."

            }), 400


        # ----------------------------------------------------
        # RUN COMPLETE VERIFICATION PIPELINE
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print(" API VERIFICATION REQUEST")
        print("=" * 60)
        print()
        print("Claim:")
        print(claim)
        print()


        result = verify_news(
            claim
        )


        # ----------------------------------------------------
        # JSON-SAFE RESULT
        # ----------------------------------------------------

        safe_result = make_json_safe(
            result
        )


        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "data":
                safe_result

        }), 200


    except Exception as error:

        print()
        print("=" * 60)
        print(" API ERROR")
        print("=" * 60)
        print(
            "Error:",
            str(error)
        )
        print()


        return jsonify({

            "success": False,

            "error":
                "Verification failed.",

            "details":
                str(error)

        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print(" MULTILINGUAL NEWS VERIFICATION API")
    print("=" * 60)
    print()
    print("Backend:")
    print("http://localhost:5000")
    print()
    print("Health:")
    print("http://localhost:5000/api/health")
    print()
    print("Verification:")
    print("POST http://localhost:5000/api/verify")
    print()
    print("=" * 60)
    print()


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )