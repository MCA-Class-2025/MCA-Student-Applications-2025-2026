import sqlite3
import re
import os
import hashlib
import hmac

# Use the same database file as the rest of the project.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "event_planner.db")


def create_user_table():
    """Create the users table if it does not already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def valid_email(email):
    """Basic email validation."""
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.fullmatch(pattern, email.strip()))


def valid_password(password):
    """
    Password must contain:
    - at least 8 characters
    - one uppercase letter
    - one lowercase letter
    - one number
    - one special character
    """
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


def hash_password(password):
    """Create a salted PBKDF2-HMAC-SHA256 password hash."""
    salt = os.urandom(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        f"pbkdf2_sha256${iterations}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password, stored_hash):
    """Verify a password against the stored PBKDF2 hash."""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def register_user(full_name, email, password, confirm_password):
    """
    Register a new user.
    Returns: (success: bool, message: str)
    """
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        return False, "Please enter your full name."

    if not email:
        return False, "Please enter your email address."

    if not valid_email(email):
        return False, "Please enter a valid email address."

    if not password:
        return False, "Please enter a password."

    if not valid_password(password):
        return (
            False,
            "Password must be at least 8 characters and contain "
            "uppercase, lowercase, number and special character."
        )

    if not confirm_password:
        return False, "Please confirm your password."

    if password != confirm_password:
        return False, "Password and Confirm Password do not match."

    create_user_table()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (full_name, email, hash_password(password))
            )
            conn.commit()

        return True, "Registration successful! You can now log in."

    except sqlite3.IntegrityError:
        return False, "This email is already registered. Please log in."


def authenticate_user(email, password):
    """
    Authenticate a user.
    Returns a dictionary on success, otherwise None.
    """
    email = email.strip().lower()

    if not email or not password:
        return None

    create_user_table()

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, name, email, password
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if row and verify_password(password, row[3]):
        return {
            "id": row[0],
            "full_name": row[1],
            "email": row[2],
            "password_hash": row[3]
        }

    return None
