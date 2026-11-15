from datetime import datetime, timedelta, timezone
from typing import Literal
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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

VALID_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
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
    xp: int = 0
    streak_days: int = 0


class SwipeInput(BaseModel):
    status: Literal["known", "learning"]


def normalized_email(email: EmailStr) -> str:
    return str(email).strip().lower()


def validate_level(level: str) -> str:
    clean = level.strip().upper()
    if clean not in VALID_LEVELS:
        raise HTTPException(400, "Invalid CEFR level")
    return clean


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
                SELECT users.id, users.email, users.xp, users.streak_days
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
                    RETURNING id, email, xp, streak_days
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
                SELECT id, email, password_hash, xp, streak_days
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
    return {
        "id": user["id"],
        "email": user["email"],
        "xp": user["xp"],
        "streak_days": user["streak_days"],
    }


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


@app.get("/levels")
def list_levels(user=Depends(current_user)):
    """Return all 6 CEFR levels with total words and how many the user completed."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                w.cefr_level,
                COUNT(w.id) AS total_words,
                COUNT(uw.word_id) FILTER (WHERE uw.status IN ('known', 'mastered')) AS completed_words
            FROM words w
                     LEFT JOIN user_words uw
                               ON uw.word_id = w.id AND uw.user_id = %s
            GROUP BY w.cefr_level
            """,
            (user["id"],),
        ).fetchall()

    by_level = {row["cefr_level"]: row for row in rows}
    return [
        {
            "level": lvl,
            "total_words": by_level.get(lvl, {}).get("total_words", 0),
            "completed_words": by_level.get(lvl, {}).get("completed_words", 0),
        }
        for lvl in VALID_LEVELS
    ]


@app.get("/levels/{level}/packs")
def list_packs(level: str, user=Depends(current_user)):
    """Return word packs in a level with per-pack progress bar counts."""
    clean_level = validate_level(level)
    with get_connection() as connection:
        packs = connection.execute(
            """
            SELECT
                w.pack_number,
                COUNT(w.id) AS total_words,
                COUNT(uw.word_id) FILTER (WHERE uw.status IN ('known', 'mastered')) AS completed_words,
                COUNT(uw.word_id) FILTER (WHERE uw.status = 'learning') AS learning_words
            FROM words w
                     LEFT JOIN user_words uw
                               ON uw.word_id = w.id AND uw.user_id = %s
            WHERE w.cefr_level = %s
            GROUP BY w.pack_number
            ORDER BY w.pack_number
            """,
            (user["id"], clean_level),
        ).fetchall()
    return packs


@app.get("/levels/{level}/packs/{pack_number}/words")
def get_pack_words(level: str, pack_number: int, user=Depends(current_user)):
    """Return all words in a specific pack along with this user's status on each word."""
    clean_level = validate_level(level)
    with get_connection() as connection:
        words = connection.execute(
            """
            SELECT
                w.id,
                w.word,
                w.cefr_level,
                w.pack_number,
                w.meaning_he,
                w.example_sentence,
                uw.status
            FROM words w
                     LEFT JOIN user_words uw
                               ON uw.word_id = w.id AND uw.user_id = %s
            WHERE w.cefr_level = %s AND w.pack_number = %s
            ORDER BY w.id
            """,
            (user["id"], clean_level, pack_number),
        ).fetchall()

    if not words:
        raise HTTPException(404, "Pack not found")
    return words


@app.post("/words/{word_id}/swipe")
def swipe_word(word_id: int, payload: SwipeInput, user=Depends(current_user)):
    """Record user's swipe decision: 'known' (left) or 'learning' (right)."""
    with get_connection() as connection:
        exists = connection.execute(
            "SELECT id FROM words WHERE id = %s",
            (word_id,),
        ).fetchone()
        if not exists:
            raise HTTPException(404, "Word not found")

        connection.execute(
            """
            INSERT INTO user_words (user_id, word_id, status, updated_at)
            VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, word_id) DO UPDATE SET
                status = EXCLUDED.status,
                                                      updated_at = NOW()
            """,
            (user["id"], word_id, payload.status),
        )
    return {"word_id": word_id, "status": payload.status}