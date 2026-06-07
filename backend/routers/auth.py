import secrets

import psycopg2.errors
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.security import check_password, get_current_user, hash_password
from ..database import dcur, get_db
from ..schemas.user import AuthResponse, LoginRequest, UserCreate, UserOut

router = APIRouter()


def _create_session(conn, user_id: int) -> str:
    token = secrets.token_hex(32)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO sessions (token, user_id) VALUES (%s, %s)", (token, user_id))
    return token


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(body: UserCreate):
    try:
        with get_db() as conn:
            with dcur(conn) as cur:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (body.name, body.email.lower(), hash_password(body.password)),
                )
                user_id = cur.fetchone()["id"]
                token = _create_session(conn, user_id)
        return {"token": token, "user": {"id": user_id, "name": body.name, "email": body.email.lower()}}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered")


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    with get_db() as conn:
        with dcur(conn) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (body.email.lower(),))
            user = cur.fetchone()
        if not user or not check_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = _create_session(conn, user["id"])
    return {"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    if credentials:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE token = %s", (credentials.credentials,))
    return {"message": "Logged out"}


@router.get("/profile", response_model=UserOut)
def profile(user: dict = Depends(get_current_user)):
    return user
