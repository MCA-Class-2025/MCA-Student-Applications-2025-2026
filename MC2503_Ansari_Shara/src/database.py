import mysql.connector


class Database:

    def __init__(self):

        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="zero_trust_system"
        )

        self.cursor = self.connection.cursor(dictionary=True)

    # ==========================================
    # Generic Fetch
    # ==========================================

    def fetch(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    # ==========================================
    # Blocked Users
    # ==========================================

    def get_blocked_users(self):

        query = """
        SELECT u.username,
               r.risk_score,
               r.threat_level
        FROM users u
        JOIN risk_assessment r
        ON u.user_id=r.user_id
        WHERE r.blocked=1
        """

        return self.fetch(query)

    # ==========================================
    # High Risk Users
    # ==========================================

    def get_high_risk_users(self):

        query = """
        SELECT u.username,
               r.risk_score,
               r.threat_level
        FROM users u
        JOIN risk_assessment r
        ON u.user_id=r.user_id
        WHERE r.threat_level='High'
        ORDER BY r.risk_score DESC
        """

        return self.fetch(query)

    # ==========================================
    # Medium Risk Users
    # ==========================================

    def get_medium_risk_users(self):

        query = """
        SELECT u.username,
               r.risk_score,
               r.threat_level
        FROM users u
        JOIN risk_assessment r
        ON u.user_id=r.user_id
        WHERE r.threat_level='Medium'
        ORDER BY r.risk_score DESC
        """

        return self.fetch(query)

    # ==========================================
    # Low Risk Users
    # ==========================================

    def get_low_risk_users(self):

        query = """
        SELECT u.username,
               r.risk_score,
               r.threat_level
        FROM users u
        JOIN risk_assessment r
        ON u.user_id=r.user_id
        WHERE r.threat_level='Low'
        ORDER BY r.risk_score DESC
        """

        return self.fetch(query)

    # ==========================================
    # Today's Risk Summary
    # ==========================================

    def get_risk_summary(self):

        query = """
        SELECT
        COUNT(*) AS total_users,
        SUM(threat_level='High') AS high_risk,
        SUM(threat_level='Medium') AS medium_risk,
        SUM(threat_level='Low') AS low_risk
        FROM risk_assessment
        """

        return self.fetch(query)

    # ==========================================
    # Failed Login Attempts
    # ==========================================

    def get_failed_logins(self):

        query = """
        SELECT
        u.username,
        r.failed_attempts
        FROM users u
        JOIN risk_assessment r
        ON u.user_id=r.user_id
        WHERE r.failed_attempts>0
        ORDER BY r.failed_attempts DESC
        """

        return self.fetch(query)

    def get_user_risk(self, username):

        query = """
        SELECT
            u.username,
            r.failed_attempts,
            r.suspicious_activity,
            r.threat_level,
            r.risk_score,
            r.decision,
            r.privilege_level,
            r.session_duration,
            r.blocked,
            r.assessment_time
        FROM users u
        JOIN risk_assessment r
            ON u.user_id = r.user_id
        WHERE u.username = %s
        ORDER BY r.assessment_time DESC
        LIMIT 1
        """

        self.cursor.execute(query, (username,))
        return self.cursor.fetchone()

    # ==========================================
    # Close Connection
    # ==========================================

    def close(self):

        self.cursor.close()
        self.connection.close()