import hashlib
from datetime import datetime, timedelta

from jose import jwt

try:
    from pwdlib import PasswordHash
    password_hash = PasswordHash.recommended()
except Exception:
    password_hash = None


SECRET_KEY = "change-this-secret-key-for-your-project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    if password_hash is not None:
        try:
            return password_hash.hash(password)
        except Exception:
            pass
    return "pbkdf2$" + hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt_key', 100000).hex()


def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    if hashed_password.startswith("pbkdf2$"):
        expected = "pbkdf2$" + hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt_key', 100000).hex()
        return expected == hashed_password
    if password_hash is not None:
        try:
            return password_hash.verify(
                password,
                hashed_password
            )
        except Exception:
            pass
    return False


def create_access_token(user_id: int):

    expire = (
        datetime.utcnow()
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )


    payload = {

        "user_id": user_id,

        "exp": expire

    }


    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )