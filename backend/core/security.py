import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import dcur, get_db

_bearer = HTTPBearer()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${pw_hash}"


def check_password(password: str, stored: str) -> bool:
    salt, pw_hash = stored.split("$", 1)
    test_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hmac.compare_digest(test_hash, pw_hash)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    token = credentials.credentials
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute(
                """
                SELECT users.id, users.name, users.email
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = %s
                """,
                (token,),
            )
            user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return dict(user)
