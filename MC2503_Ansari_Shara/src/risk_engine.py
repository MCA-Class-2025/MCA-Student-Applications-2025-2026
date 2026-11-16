from utils import (
    load_risk_rules,
    calculate_session_score,
    calculate_failed_attempt_score,
    calculate_risk_level
)


class RiskEngine:

    def __init__(self):
        self.rules = load_risk_rules()

    def calculate_risk(self, record):

        score = 0
        reasons = []

        # -----------------------------
        # Failed Attempts
        # -----------------------------
        failed_attempts = int(record["failed_attempts"])

        failed_score = calculate_failed_attempt_score(
            failed_attempts,
            self.rules
        )

        score += failed_score

        if failed_score > 0:
            reasons.append(f"{failed_attempts} failed login attempts")

        # -----------------------------
        # Login Success
        # -----------------------------
        success = str(record["success"])

        score += self.rules["success"][success]

        if success == "False":
            reasons.append("Login failed")

        # -----------------------------
        # Account Status
        # -----------------------------
        account_status = record["account_status"]

        score += self.rules["account_status"][account_status]

        if account_status != "Active":
            reasons.append(f"Account is {account_status}")

        # -----------------------------
        # Role
        # -----------------------------
        role = record["role"]

        score += self.rules["role"][role]

        if role == "Admin":
            reasons.append("Administrator account")

        # -----------------------------
        # Session Duration
        # -----------------------------
        session_duration = int(record["session_duration"])

        session_score = calculate_session_score(
            session_duration,
            self.rules
        )

        score += session_score

        if session_score > 0:
            reasons.append("Long session duration")

        # -----------------------------
        # Limit Maximum Score
        # -----------------------------
        score = min(score, 100)

        risk_level = calculate_risk_level(score)

        # -----------------------------
        # Generate Threat Level
        # -----------------------------
        if score <= 30:
            threat_level = "Low"
            suspicious_activity = "No"
            recommended_action = "Allow Login"

        elif score <= 60:
            threat_level = "Medium"
            suspicious_activity = "Yes"
            recommended_action = (
                "Allow Login and Send Security Alert to User. "
                "Recommend Password Change."
            )

        else:
            threat_level = "High"
            suspicious_activity = True
            recommended_action = (
                "Block Login, Notify Administrator, "
                "and Recommend Immediate Password Reset."
            )
        return {
            "risk_score": score,
            "risk_level": risk_level,
            "threat_level": threat_level,
            "suspicious_activity": suspicious_activity,
            "recommended_action": recommended_action,
            "reasons": reasons
        }