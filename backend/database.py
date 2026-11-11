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
        # 1. Users table (authentication + level, goals, and gamification)
        """
        CREATE TABLE IF NOT EXISTS users (
                                             id BIGSERIAL PRIMARY KEY,
                                             email TEXT NOT NULL UNIQUE,
                                             password_hash TEXT NOT NULL,
                                             cefr_level TEXT NOT NULL DEFAULT 'B1',
                                             learning_goal TEXT NOT NULL DEFAULT 'daily',
                                             xp INTEGER NOT NULL DEFAULT 0,
                                             streak_days INTEGER NOT NULL DEFAULT 0,
                                             last_practice_date DATE,
                                             created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """,
        # Safely add the new columns if the users table was already created earlier
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS cefr_level TEXT NOT NULL DEFAULT 'B1',
            ADD COLUMN IF NOT EXISTS learning_goal TEXT NOT NULL DEFAULT 'daily',
            ADD COLUMN IF NOT EXISTS xp INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS streak_days INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_practice_date DATE
        """,
        # 2. Active login sessions
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
        # 3. Skill Graph Nodes: both vocabulary words and grammar rules
        """
        CREATE TABLE IF NOT EXISTS skills (
                                              id BIGSERIAL PRIMARY KEY,
                                              code TEXT NOT NULL UNIQUE,
                                              name TEXT NOT NULL,
                                              skill_type TEXT NOT NULL CHECK (skill_type IN ('vocab', 'grammar')),
            cefr_level TEXT NOT NULL,
            pack_number INTEGER,
            meaning_he TEXT NOT NULL DEFAULT '',
            example_sentence TEXT NOT NULL DEFAULT '',
            severity INTEGER NOT NULL DEFAULT 1
            )
        """,
        """
        CREATE INDEX IF NOT EXISTS skills_level_pack_index
            ON skills(cefr_level, pack_number)
        """,
        # 4. Skill Graph Edges: prerequisite relationships (DAG)
        """
        CREATE TABLE IF NOT EXISTS skill_prerequisites (
                                                           skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            prerequisite_skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            PRIMARY KEY (skill_id, prerequisite_skill_id),
            CHECK (skill_id != prerequisite_skill_id)
            )
        """,
        # 5. Per-user mastery and error tracking across all skills
        """
        CREATE TABLE IF NOT EXISTS user_skills (
                                                   user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'learning'
            CHECK (status IN ('learning', 'known', 'mastered')),
            mastery_score INTEGER NOT NULL DEFAULT 0,
            practice_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            last_practiced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, skill_id)
            )
        """,
        """
        CREATE INDEX IF NOT EXISTS user_skills_user_id_index
            ON user_skills(user_id)
        """,
        # 6. Context-aware speaking prompts matched by level, goal, and grammar rule
        """
        CREATE TABLE IF NOT EXISTS practice_prompts (
                                                        id BIGSERIAL PRIMARY KEY,
                                                        cefr_level TEXT NOT NULL,
                                                        learning_goal TEXT NOT NULL DEFAULT 'general',
                                                        grammar_skill_code TEXT,
                                                        prompt_template TEXT NOT NULL
        )
        """,
    )
    with get_connection() as connection:
        for statement in statements:
            connection.execute(statement)


if __name__ == "__main__":
    initialize_database()
    print("Database tables are ready")