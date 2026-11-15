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
        # 1. Users (account + daily streak + XP)
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0,
            streak_days INTEGER NOT NULL DEFAULT 0,
            last_practice_date DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        # 2. Active login sessions (Cookie -> user_id)
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
        # 3. Vocabulary words divided into shuffled packs per CEFR level (A1-C2)
        """
        CREATE TABLE IF NOT EXISTS words (
            id BIGSERIAL PRIMARY KEY,
            word TEXT NOT NULL,
            cefr_level TEXT NOT NULL,
            pack_number INTEGER NOT NULL,
            meaning_he TEXT NOT NULL,
            example_sentence TEXT NOT NULL,
            UNIQUE (cefr_level, word)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS words_level_pack_index
            ON words(cefr_level, pack_number)
        """,
        # 4. Grammar rules (Nodes in our Skill Graph)
        """
        CREATE TABLE IF NOT EXISTS grammar_rules (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            cefr_level TEXT NOT NULL,
            severity INTEGER NOT NULL DEFAULT 1,
            explanation_he TEXT NOT NULL,
            example_sentence TEXT NOT NULL,
            followup_prompt TEXT NOT NULL
        )
        """,
        # 5. Grammar prerequisite edges (Skill Graph DAG)
        """
        CREATE TABLE IF NOT EXISTS grammar_prerequisites (
            rule_id BIGINT NOT NULL REFERENCES grammar_rules(id) ON DELETE CASCADE,
            prerequisite_rule_id BIGINT NOT NULL REFERENCES grammar_rules(id) ON DELETE CASCADE,
            PRIMARY KEY (rule_id, prerequisite_rule_id),
            CHECK (rule_id != prerequisite_rule_id)
        )
        """,
        # 6. Per-user vocabulary progress (known / learning / mastered)
        """
        CREATE TABLE IF NOT EXISTS user_words (
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            word_id BIGINT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK (status IN ('known', 'learning', 'mastered')),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, word_id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS user_words_user_id_index
            ON user_words(user_id)
        """,
        # 7. Per-user grammar mastery & recurring errors (feeds Priority Queue)
        """
        CREATE TABLE IF NOT EXISTS user_grammar_stats (
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rule_id BIGINT NOT NULL REFERENCES grammar_rules(id) ON DELETE CASCADE,
            error_count INTEGER NOT NULL DEFAULT 0,
            mastery_score INTEGER NOT NULL DEFAULT 50,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, rule_id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS user_grammar_stats_user_id_index
            ON user_grammar_stats(user_id)
        """,
    )
    with get_connection() as connection:
        for statement in statements:
            connection.execute(statement)


if __name__ == "__main__":
    initialize_database()
    print("Database tables are ready")