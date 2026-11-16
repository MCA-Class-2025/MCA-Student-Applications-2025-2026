import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import json

# ------------------------------------------
# AI Backend Location
# ------------------------------------------

AI_PROJECT = r"D:\Shara\Responsible_AI_Risk_Assessment"

SRC = os.path.join(AI_PROJECT, "src")

sys.path.insert(0, SRC)

os.chdir(AI_PROJECT)

# ------------------------------------------
# Imports
# ------------------------------------------

from database import Database
from rag_engine import RAGEngine
from llm_engine import LLMEngine
from chatbot import ChatBot

# ------------------------------------------
# Initialize
# ------------------------------------------

bot = ChatBot()
db = Database()
rag = RAGEngine()
llm = LLMEngine()

question = sys.argv[1]

intent = bot.detect_intent(question)

# ------------------------------------------
# USER RISK
# ------------------------------------------

if intent == "user_risk":

    username = bot.extract_username(question)

    user = db.get_user_risk(username)

    if user is None:

        print(json.dumps({
            "status": "error",
            "message": "User not found."
        }))

        sys.exit()

    knowledge = rag.get_policy(user)

    answer = llm.explain_user_risk(
        user,
        question,
        knowledge
    )

    print(json.dumps({

        "status": "success",

        "raw": {

            "Username": user["username"],
            "Risk Score": user["risk_score"],
            "Threat Level": user["threat_level"],
            "Failed Attempts": user["failed_attempts"],
            "Session Duration": user["session_duration"],
            "Suspicious Activity": "Yes" if user["suspicious_activity"] else "No",
            "Blocked": "Yes" if user["blocked"] else "No"

        },

        "answer": answer

    }))

else:

    print(json.dumps({

        "status": "error",

        "message": "Unsupported question."

    }))