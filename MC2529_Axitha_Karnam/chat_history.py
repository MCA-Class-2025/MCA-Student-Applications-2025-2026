import csv
import os
from datetime import datetime


# ============================================================
# CHAT HISTORY CSV FILE
# ============================================================

CHAT_HISTORY_FILE = "chat_history.csv"


# ============================================================
# SAVE CHAT MESSAGE
# ============================================================

def save_chat_message(
    user_message,
    assistant_message,
    chat_type="general",
    source="Finance AI"
):
    """
    Save one complete chat interaction into CSV.

    Columns:
        ID
        Timestamp
        Type
        Source
        User Question
        AI Answer
    """

    try:

        # ----------------------------------------------------
        # CHECK IF CSV FILE ALREADY EXISTS
        # ----------------------------------------------------

        file_exists = os.path.exists(
            CHAT_HISTORY_FILE
        )

        # ----------------------------------------------------
        # OPEN CSV FILE
        # ----------------------------------------------------

        with open(
            CHAT_HISTORY_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            # ------------------------------------------------
            # CREATE HEADER FOR NEW FILE
            # ------------------------------------------------

            if not file_exists:

                writer.writerow([
                    "ID",
                    "Timestamp",
                    "Type",
                    "Source",
                    "User Question",
                    "AI Answer"
                ])

            # ------------------------------------------------
            # GENERATE ID
            # ------------------------------------------------

            record_id = get_next_id()

            # ------------------------------------------------
            # CURRENT DATE AND TIME
            # ------------------------------------------------

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ------------------------------------------------
            # SAVE CHAT
            # ------------------------------------------------

            writer.writerow([
                record_id,
                timestamp,
                chat_type,
                source,
                user_message,
                assistant_message
            ])

    except Exception as error:

        print(
            "Error saving chat history:",
            error
        )


# ============================================================
# GET NEXT CHAT ID
# ============================================================

def get_next_id():
    """
    Return the next available ID for the CSV file.
    """

    if not os.path.exists(
        CHAT_HISTORY_FILE
    ):

        return 1

    try:

        with open(
            CHAT_HISTORY_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            last_id = 0

            for row in reader:

                try:

                    current_id = int(
                        row.get("ID", 0)
                    )

                    if current_id > last_id:

                        last_id = current_id

                except (
                    ValueError,
                    TypeError
                ):

                    continue

            return last_id + 1

    except Exception as error:

        print(
            "Error reading chat history:",
            error
        )

        return 1


# ============================================================
# GET ALL CHAT HISTORY
# ============================================================

def get_chat_history():
    """
    Return all saved chat conversations.

    Returns:
        list of dictionaries
    """

    if not os.path.exists(
        CHAT_HISTORY_FILE
    ):

        return []

    try:

        with open(
            CHAT_HISTORY_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            history = list(reader)

            return history

    except Exception as error:

        print(
            "Error loading chat history:",
            error
        )

        return []


# ============================================================
# CLEAR CHAT HISTORY
# ============================================================

def clear_chat_history():
    """
    Delete the complete chat history CSV file.
    """

    try:

        if os.path.exists(
            CHAT_HISTORY_FILE
        ):

            os.remove(
                CHAT_HISTORY_FILE
            )

            return True

        return False

    except Exception as error:

        print(
            "Error clearing chat history:",
            error
        )

        return False