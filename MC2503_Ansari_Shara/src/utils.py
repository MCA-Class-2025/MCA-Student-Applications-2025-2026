import json


def load_risk_rules():
    """
    Load risk scoring rules from JSON file.
    """

    with open("config/risk_rules.json", "r") as file:
        rules = json.load(file)

    return rules


def calculate_session_score(session_duration, rules):
    """
    Calculate score based on session duration.
    """

    score = 0

    if session_duration >= 3000:
        score = rules["session_duration"]["3000"]

    elif session_duration >= 2000:
        score = rules["session_duration"]["2000"]

    elif session_duration >= 1000:
        score = rules["session_duration"]["1000"]

    return score


def calculate_failed_attempt_score(failed_attempts, rules):
    """
    Gradually increase score after the first failed attempt.
    """

    start = rules["failed_attempt_start"]
    increment = rules["failed_attempt_increment"]

    if failed_attempts < start:
        return 0

    return (failed_attempts - 1) * increment


def calculate_risk_level(score):
    """
    Convert score into Low, Medium or High.
    """

    if score <= 30:
        return "Low"

    elif score <= 60:
        return "Medium"

    return "High"