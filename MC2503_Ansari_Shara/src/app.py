from flask import Flask, request, jsonify

from database import Database
from rag_engine import RAGEngine
from llm_engine import LLMEngine
from chatbot import ChatBot

app = Flask(__name__)

print("Loading AI Security Assistant...")

bot = ChatBot()
db = Database()
rag = RAGEngine()
llm = LLMEngine()

print("AI Assistant Ready!")


@app.route("/chat", methods=["POST"])
def chat():

    print("========== NEW REQUEST ==========", flush=True)

    data = request.get_json()
    print("DATA:", data, flush=True)

    question = data.get("question", "").strip()
    print("QUESTION:", question, flush=True)

    if question == "":
        return jsonify({
            "status": "error",
            "message": "Question cannot be empty."
        })

    intent = bot.detect_intent(question)
    print("INTENT:", intent, flush=True)

    # -----------------------------------------
    # USER RISK
    # -----------------------------------------

    if intent == "user_risk":

        username = bot.extract_username(question)

        user = db.get_user_risk(username)

        if user is None:

            return jsonify({
                "status": "error",
                "message": "User not found."
            })

        knowledge = rag.get_policy(user)

        answer = llm.explain_user_risk(
            user,
            question,
            knowledge
        )

        return jsonify({

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

        })


    # -----------------------------------------
    # HIGH RISK USERS
    # -----------------------------------------

    elif intent == "high_risk_users":

        users = db.get_high_risk_users()

        answer = ""

        for u in users:

            answer += (
                f"👤 {u['username']}\n"
                f"Risk Score: {u['risk_score']}\n"
                f"Threat Level: {u['threat_level']}\n\n"

                "Explanation\n"
                "This user is classified as High Risk because of the high risk score and requires immediate administrator attention.\n\n"

                "Recommendation\n"
                "• Verify the user's identity.\n"
                "• Notify the administrator.\n"
                "• Restrict access until the account is reviewed.\n\n"
            )

        return jsonify({
            "status": "success",
            "answer": answer
        })


    # -----------------------------------------
    # MEDIUM RISK USERS
    # -----------------------------------------

    elif intent == "medium_risk_users":

        users = db.get_medium_risk_users()

        return jsonify({

            "status": "success",

            "answer": "\n\n".join(

                [
                    f"👤 {u['username']}\n"
                    f"Risk Score: {u['risk_score']}\n"
                    f"Threat Level: {u['threat_level']}\n\n"
                    
                    "Explanation\n"
                    "The user should be monitored closely.\n\n"
                    
                    "Recommendation\n"
                    "Continue monitoring, recommend password change.\n\n"
                ]

            )

        })


    # -----------------------------------------
    # LOW RISK USERS
    # -----------------------------------------

    elif intent == "low_risk_users":

        users = db.get_low_risk_users()

        return jsonify({

            "status": "success",

            "answer": "\n\n".join(

                [
                    f"👤 {u['username']}\n"
                    f"Risk Score: {u['risk_score']}\n"
                    f"Threat Level: {u['threat_level']}\n\n"
                                        
                    "Explanation\n"
                    "No suspicious activity detected.\n\n"
                                        
                    "Recommendation\n"
                    "Allow access and continue routine monitoring.\n\n"
                ]

            )

        })


    # -----------------------------------------
    # BOCKED USERS
    # -----------------------------------------

    elif intent == "blocked_users":

        users = db.get_blocked_users()

        if not users:

            return jsonify({
                "status": "success",
                "answer": "No Blocked users found."
            })

        answer = "🚫 Blocked Users\n\n"

        for u in users:

            answer += (
                f"👤 {u['username']}\n"
                f"Risk Score: {u['risk_score']}\n"
                f"Threat Level: {u['threat_level']}\n\n"
                                                        
                "Explanation\n"
                "The account has been blocked due to security policy"
                                                        
                "Recommendation\n"
                "Keep the account blocked until verified."
            )

        return jsonify({
            "status": "success",
            "answer": answer
        })


    # -----------------------------------------
    # FAILED LOGINS
    # -----------------------------------------

    elif intent == "failed_logins":

        users = db.get_failed_logins()

        return jsonify({

            "status": "success",

            "answer": "\n".join(

                [
                    f"{u['username']} - {u['failed_attempts']} failed login attempts"
                    for u in users
                ]

            )

        })


    # -----------------------------------------
    # RISK SUMMARY
    # -----------------------------------------

    elif intent == "risk_summary":

        s = db.get_risk_summary()[0]

        return jsonify({

            "status": "success",

            "answer":
            f"""📊 Risk Summary

            Total Users: {s['total_users']}

            High Risk: {s['high_risk']}

            Medium Risk: {s['medium_risk']}

            Low Risk: {s['low_risk']}"""

        })


    # -----------------------------------------
    # UNKNOWN
    # -----------------------------------------

    else:

        return jsonify({

            "status": "error",

            "message": "Unsupported question."

        })

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )