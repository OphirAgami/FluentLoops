from datetime import datetime, timedelta, timezone
import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from database import get_connection
from security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

app = FastAPI(title="FluentLoop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

SESSION_COOKIE = "fluentloop_session"
SESSION_DAYS = 7
SESSION_SECONDS = SESSION_DAYS * 24 * 60 * 60
DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")

class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOutput(BaseModel):
    id: int
    email: EmailStr

def normalized_email(email: EmailStr) -> str:
    return str(email).strip().lower()

def create_session(connection, user_id: int) -> str:
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)

    connection.execute("DELETE FROM sessions WHERE expires_at <= NOW()")
    connection.execute(
        """
        INSERT INTO sessions (token_hash, user_id, expires_at)
        VALUES (%s, %s, %s)
        """,
        (token_hash, user_id, expires_at),
    )
    return raw_token

def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

def current_user(request: Request):
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in",
        )
    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                SELECT users.id, users.email
                FROM sessions
                         JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = %s
                  AND sessions.expires_at > NOW()
                """,
                (hash_session_token(raw_token),),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise HTTPException(503, "Database unavailable") from None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    return user

@app.get("/health")
def health():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except (psycopg.Error, RuntimeError):
        raise HTTPException(503, "Database unavailable") from None
    return {"status": "ok", "database": "connected"}

@app.post(
    "/auth/register",
    response_model=UserOutput,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: AuthInput, response: Response):
    email = normalized_email(payload.email)
    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                    RETURNING id, email
                """,
                (email, hash_password(payload.password)),
            ).fetchone()
            session_token = create_session(connection, user["id"])
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "An account with this email already exists") from None
    except (psycopg.Error, RuntimeError):
        raise HTTPException(503, "Database unavailable") from None

    set_session_cookie(response, session_token)
    return user

@app.post("/auth/login", response_model=UserOutput)
def login(payload: AuthInput, response: Response):
    email = normalized_email(payload.email)
    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                SELECT id, email, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            ).fetchone()

            stored_hash = user["password_hash"] if user else DUMMY_PASSWORD_HASH
            password_matches = verify_password(payload.password, stored_hash)

            if not user or not password_matches:
                raise HTTPException(401, "Invalid email or password")

            session_token = create_session(connection, user["id"])
    except HTTPException:
        raise
    except (psycopg.Error, RuntimeError):
        raise HTTPException(503, "Database unavailable") from None

    set_session_cookie(response, session_token)
    return {"id": user["id"], "email": user["email"]}

@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response):
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        try:
            with get_connection() as connection:
                connection.execute(
                    "DELETE FROM sessions WHERE token_hash = %s",
                    (hash_session_token(raw_token),),
                )
        except (psycopg.Error, RuntimeError):
            raise HTTPException(503, "Database unavailable") from None

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        samesite="lax",
        secure=False,
    )

@app.get("/auth/me", response_model=UserOutput)
def me(user=Depends(current_user)):
    return user