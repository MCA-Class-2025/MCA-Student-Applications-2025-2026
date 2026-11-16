from database import Database
from rag_engine import RAGEngine
from llm_engine import LLMEngine
class ChatBot:

    def __init__(self):
        pass

    # ==========================================
    # Detect User Intent
    # ==========================================

    def detect_intent(self, question):

        question = question.lower()

        # -----------------------------
        # Blocked Users
        # -----------------------------
        if "blocked" in question:
            return "blocked_users"

        # -----------------------------
        # User Risk
        # -----------------------------
        elif "why is" in question or "explain" in question:

            return "user_risk"
        
        # -----------------------------
        # High Risk Users
        # -----------------------------
        elif "high risk" in question:
            return "high_risk_users"

        # -----------------------------
        # Medium Risk Users
        # -----------------------------
        elif "medium risk" in question:
            return "medium_risk_users"

        # -----------------------------
        # Low Risk Users
        # -----------------------------
        elif "low risk" in question:
            return "low_risk_users"

        # -----------------------------
        # Risk Summary
        # -----------------------------
        elif "summary" in question:
            return "risk_summary"
        
        # -----------------------------
        # Failed Logins
        # -----------------------------
        elif "failed" in question:
            return "failed_logins"

        
        # -----------------------------
        # Unknown
        # -----------------------------
        else:
            return "unknown"

    # ==========================================
    # Decide Data Source
    # ==========================================

    def get_data_source(self, intent):

        database_intents = [
            "blocked_users",
            "high_risk_users",
            "medium_risk_users",
            "low_risk_users",
            "risk_summary",
            "failed_logins",
            "user_risk"
        ]


        if intent in database_intents:
            return "database"

        else:
            return "unknown"

    def extract_username(self, question):

        words = question.split()

        ignore = {
            "why", "is", "explain", "risk", "high",
            "low", "medium", "user", "should",
            "be", "allowed", "access", "give",
            "recommendation", "for", "flagged"
        }

        for word in words:

            clean = word.strip("?,.!")

            # Remove possessive 's
            if clean.endswith("'s"):
                clean = clean[:-2]

            if clean.lower() not in ignore:
                return clean.capitalize()

        return None
# ==========================================
# Testing
# ==========================================

if __name__ == "__main__":

    bot = ChatBot()
    db = Database()
    rag = RAGEngine()
    llm = LLMEngine()

    print("=" * 60)
    print("SECURESHARE AI SECURITY ASSISTANT")
    print("=" * 60)

    while True:

        question = input("\nAsk: ")

        if question.lower() == "exit":
            print("\nGoodbye!")
            break

        intent = bot.detect_intent(question)
        source = bot.get_data_source(intent)

        print("\nIntent      :", intent)
        print("Data Source :", source)

        # ==========================================
        # BLOCKED USERS
        # ==========================================

        if intent == "blocked_users":

            users = db.get_blocked_users()

            print("\nBlocked Users")
            print("-" * 40)

            if len(users) == 0:
                print("No blocked users found.")

            else:

                for user in users:

                    print(
                        f"Username : {user['username']}\n"
                        f"Risk Score : {user['risk_score']}\n"
                        f"Threat Level : {user['threat_level']}\n"
                    )

        # ==========================================
        # HIGH RISK USERS
        # ==========================================

        elif intent == "high_risk_users":

            users = db.get_high_risk_users()

            print("\nHigh Risk Users")
            print("-" * 40)

            if len(users) == 0:
                print("No high risk users found.")

            else:

                for user in users:

                    print(
                        f"Username : {user['username']}\n"
                        f"Risk Score : {user['risk_score']}\n"
                        f"Threat Level : {user['threat_level']}\n"
                    )

        # ==========================================
        # MEDIUM RISK USERS
        # ==========================================

        elif intent == "medium_risk_users":

            users = db.get_medium_risk_users()

            print("\nMedium Risk Users")
            print("-" * 40)

            if len(users) == 0:
                print("No medium risk users found.")

            else:

                for user in users:

                    print(
                        f"Username : {user['username']}\n"
                        f"Risk Score : {user['risk_score']}\n"
                        f"Threat Level : {user['threat_level']}\n"
                    )

        # ==========================================
        # LOW RISK USERS
        # ==========================================

        elif intent == "low_risk_users":

            users = db.get_low_risk_users()

            print("\nLow Risk Users")
            print("-" * 40)

            if len(users) == 0:
                print("No low risk users found.")

            else:

                for user in users:

                    print(
                        f"Username : {user['username']}\n"
                        f"Risk Score : {user['risk_score']}\n"
                        f"Threat Level : {user['threat_level']}\n"
                    )

        # ==========================================
        # RISK SUMMARY
        # ==========================================

        elif intent == "risk_summary":

            summary = db.get_risk_summary()

            print("\nToday's Risk Summary")
            print("-" * 40)

            if len(summary) > 0:

                s = summary[0]

                print(f"Total Users : {s['total_users']}")
                print(f"High Risk : {s['high_risk']}")
                print(f"Medium Risk : {s['medium_risk']}")
                print(f"Low Risk : {s['low_risk']}")

        # ==========================================
        # FAILED LOGINS
        # ==========================================

        elif intent == "failed_logins":

            users = db.get_failed_logins()

            print("\nFailed Login Attempts")
            print("-" * 40)

            if len(users) == 0:
                print("No failed login attempts.")

            else:

                for user in users:

                    print(
                        f"{user['username']} - {user['failed_attempts']} failed attempts"
                    )

        # ==========================================
        # USER RISK
        # ==========================================

        elif intent == "user_risk":

            username = bot.extract_username(question)
            print("Extracted Username:", username)

            user = db.get_user_risk(username)

            if user is None:

                print("\nUser not found.")

            else:

                print("\nUser Details")
                print("-" * 40)

                print(f"Username              : {user['username']}")
                print(f"Risk Score            : {user['risk_score']}")
                print(f"Threat Level          : {user['threat_level']}")
                print(f"Failed Attempts       : {user['failed_attempts']}")
                print(f"Session Duration      : {user['session_duration']}")
                print(f"Suspicious Activity   : {'Yes' if user['suspicious_activity'] else 'No'}")
                print(f"Blocked               : {'Yes' if user['blocked'] else 'No'}")

                # ----------------------------------
                # Retrieve Relevant Policies (RAG)
                # ----------------------------------

                knowledge = rag.get_policy(user)

                print("\nGenerating AI response...")

                answer = llm.explain_user_risk(
                    user,
                    question,
                    knowledge
                )

                print("AI generation completed.")
                print("\nAI Assistant")
                print("-" * 40)
                print(answer)

        # ==========================================
        # UNKNOWN
        # ==========================================

        else:

            print("\nI can only answer questions related to SecureShare security.")