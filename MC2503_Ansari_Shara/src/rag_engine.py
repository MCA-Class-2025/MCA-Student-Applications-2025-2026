import os


class RAGEngine:

    def __init__(self):

        self.folder = "knowledge_base"

    def get_policy(self, user):

        knowledge = ""

        # ----------------------------------
        # Risk Level Policy
        # ----------------------------------

        threat = user["threat_level"]

        if threat == "Low":
            files = ["low_risk_policy.txt"]

        elif threat == "Medium":
            files = ["medium_risk_policy.txt"]

        else:
            files = ["high_risk_policy.txt"]

        # ----------------------------------
        # Failed Login Policy
        # ----------------------------------

        if user["failed_attempts"] >= 3:
            files.append("failed_login_policy.txt")

        # ----------------------------------
        # Long Session Policy
        # ----------------------------------

        if user["session_duration"] >= 1200:
            files.append("long_session_policy.txt")

        # ----------------------------------
        # Blocked User Policy
        # ----------------------------------

        if user["blocked"]:
            files.append("blocked_user_policy.txt")

        # ----------------------------------
        # Recommendation Policy
        # ----------------------------------

        files.append("recommendation_policy.txt")

        # ----------------------------------
        # Retrieve Knowledge
        # ----------------------------------

        for file in files:

            path = os.path.join(self.folder, file)

            with open(path, "r", encoding="utf-8") as f:

                knowledge += f.read()
                knowledge += "\n\n"

        return knowledge