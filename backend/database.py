from pathlib import Path
import os
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv(Path(__file__).with_name(".env"))

def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing")
    return database_url

def get_connection():
    return psycopg.connect(get_database_url(), row_factory=dict_row)

def initialize_database() -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS users (
                                             id BIGSERIAL PRIMARY KEY,
                                             email TEXT NOT NULL UNIQUE,
                                             password_hash TEXT NOT NULL,
                                             created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
                                                token_hash TEXT PRIMARY KEY,
                                                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """,
        """
        CREATE INDEX IF NOT EXISTS sessions_user_id_index
            ON sessions(user_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS sessions_expires_at_index
            ON sessions(expires_at)
        """,
    )
    with get_connection() as connection:
        for statement in statements:
            connection.execute(statement)

if __name__ == "__main__":
    initialize_database()
    print("Database tables are ready")