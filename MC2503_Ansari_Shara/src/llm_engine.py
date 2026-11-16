from transformers import pipeline


class LLMEngine:

    def __init__(self):
        # Keeping pipeline for future use
        self.generator = pipeline(
            "text-generation",
            model="Qwen/Qwen2.5-1.5B-Instruct"
        )

    def explain_user_risk(self, user, question, knowledge):

        response = f"🔒 Security Analysis for {user['username']}\n\n"

        response += f"Risk Score: {user['risk_score']}\n"
        response += f"Threat Level: {user['threat_level']}\n"
        response += f"Failed Login Attempts: {user['failed_attempts']}\n"
        response += f"Session Duration: {user['session_duration']} seconds\n"
        response += f"Suspicious Activity: {'Yes' if user['suspicious_activity'] else 'No'}\n"
        response += f"Account Status: {'Blocked' if user['blocked'] else 'Active'}\n\n"

        response += "Explanation\n"

        if user["threat_level"] == "High":

            response += (
                "This user has been classified as High Risk because the security "
                "assessment detected behaviour that may threaten the system. "
                "Immediate administrator attention is recommended.\n\n"
            )

            recommendation = (
                "• Notify the administrator immediately.\n"
                "• Investigate recent login activity.\n"
                "• Review the account before allowing sensitive operations."
            )

        elif user["threat_level"] == "Medium":

            response += (
                "This user has been classified as Medium Risk. While no critical "
                "threat has been detected, additional verification is recommended "
                "to reduce potential security risks.\n\n"
            )

            recommendation = (
                "• Allow login with caution.\n"
                "• Monitor future login activity.\n"
                "• Recommend a password change."
            )

        else:

            response += (
                "This user has been classified as Low Risk. No suspicious "
                "activity or failed login attempts were detected, indicating "
                "normal account behaviour.\n\n"
            )

            recommendation = (
                "• Allow access.\n"
                "• Continue routine monitoring.\n"
                "• No administrator action is required."
            )

        # Extra explanation based on user's data
        if user["session_duration"] > 1800:
            response += (
                "\nObservation:\n"
                "The session duration is longer than normal. "
                "Although the current risk remains unchanged, "
                "extended sessions should be monitored.\n"
            )

        if user["failed_attempts"] > 0:
            response += (
                "\nObservation:\n"
                "Previous failed login attempts were detected. "
                "This should continue to be monitored.\n"
            )

        if user["suspicious_activity"]:
            response += (
                "\nObservation:\n"
                "Suspicious activity has been recorded for this user.\n"
            )

        response += "\nRecommendation\n"
        response += recommendation

        return response