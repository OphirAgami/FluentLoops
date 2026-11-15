# 🗣️ FluentLoop

**From unfamiliar words and recurring mistakes to targeted English speaking practice.**

> In development. Current milestone: authenticated CEFR vocabulary packs and swipe-based discovery backed by PostgreSQL.

## Why I'm Building FluentLoop

While improving my spoken English, I kept running into two problems:

- **Expanding my active vocabulary:** I needed a way to discover words beyond the ones I already knew and learn to use them naturally in conversation.
- **Making grammar corrections stick:** I could understand a correction and still repeat the same mistake later.

I'm building FluentLoop to turn these challenges into a personal practice plan. The experience starts with vocabulary decks: learners pick any CEFR level (`A1–C2`), swipe through shuffled word packs, filter out familiar words, and collect 5 unfamiliar ones for active speaking practice. Recurring grammar mistakes made during speaking sessions then guide targeted follow-up questions.

The goal is to track whether learners can use new vocabulary and corrected grammar patterns independently, across different situations and learning sessions.

## Current Prototype

- [x] React/TypeScript frontend with Vite and responsive gamified UI.
- [x] Secure user registration, login, logout, and session restoration (`Argon2` + `HTTPOnly` cookies + `SHA-256` hashed session tokens in PostgreSQL).
- [x] PostgreSQL schema for shuffled CEFR word packs (`words`, `user_words`) and the grammar dependency graph (`grammar_rules`, `grammar_prerequisites`, `user_grammar_stats`).
- [x] Interactive CEFR level selector (`A1–C2`), per-pack progress bars, and 5-word swipe deck persisted per user.

Explore the [frontend client](https://www.google.com/search?q=frontend/src/App.tsx), [FastAPI backend](https://www.google.com/search?q=backend/main.py), [database schema](https://www.google.com/search?q=backend/database.py), and [seed script](https://www.google.com/search?q=backend/seed_data.py), or follow the local setup instructions below.

## Planned Learning Loop

1. **Discover:** Choose any target CEFR level (`A1–C2`), review shuffled vocabulary packs, and separate familiar words from 5 unfamiliar target words.
2. **Practice:** Review meanings and examples for the 5 selected words, then answer short speaking prompts out loud using browser speech recognition.
3. **Review:** Receive vocabulary and grammar feedback after each spoken response, including corrected sentences and clear explanations. Recurring grammar errors are mapped to specific grammar rules.
4. **Adapt:** Rank recurring weaknesses in a priority queue based on error frequency, severity, and prerequisite relationships in the grammar graph.
5. **Retest:** Practice a standalone follow-up speaking prompt targeting the highest-priority grammar gap (or its foundational prerequisite skill) and update mastery, XP, and daily streaks.

For example, if a learner says **"I have went through this before,"** the feedback highlights **"I have gone through this before."** Repeated errors in Present Perfect raise its priority score—and if the learner continues to struggle, the engine traverses the prerequisite graph to check mastery of **Past Participle (`V3`)** forms first.

**Design principle:** a swipe is a self-assessment; progress reflects active usage across speaking sessions.

## Planned Engineering Design

| Engineering challenge | Approach and purpose |
| --- | --- |
| Keep progress persistent and specific to each learner | Store users, sessions, word statuses, and grammar statistics in PostgreSQL, checking session authorization on every read and write. |
| Prevent confusion between similar words | Deterministically shuffle words within each CEFR level at seed time and partition into equal-sized packs (`pack_number`). |
| Decide what to practice next | Use a **priority queue (`heapq`)** with an explicit scoring heuristic based on error recurrence, rule severity, and prerequisite impact. |
| Identify gaps in foundational skills | Represent grammar dependencies as a **directed acyclic graph (DAG)** (`grammar_prerequisites`) and traverse prerequisite links to select follow-up checks. |

## Technology

**In use:** React, TypeScript, Vite, Python, FastAPI, PostgreSQL, `psycopg`, `pwdlib` (Argon2).

**Next up:** Browser Web Speech API transcription and language-model grammar feedback.

**Later infrastructure milestones:** Docker, CI/CD, and deployment to Google Cloud Platform (GCP).

## Run the Current Prototype

Prerequisites: Node.js LTS with npm, Python 3.11 or newer, PostgreSQL, and Git. The commands below are for macOS/Linux.

### 1. Clone the repository

```bash
git clone https://github.com/OphirAgami/FluentLoop.git
cd FluentLoop
```

### 2. Configure, seed, and start the backend

Create `backend/.env` based on `backend/.env.example`, then run in the first terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: <http://localhost:8000/docs>.

### 3. Start the frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm ci
npm run dev -- --port 5173 --strictPort
```

Open <http://localhost:5173> in your browser.

## Roadmap Milestones

First learning flow with saved, per-user progress:

- [x] User registration, login, and logout.
- [x] CEFR level selection (`A1–C2`) and shuffled vocabulary packs.
- [x] Per-user vocabulary status and live pack progress bars.
- [ ] Priority-queue adaptive grammar engine (`adaptive_engine.py`).
- [ ] Speaking practice with microphone transcription, feedback, and daily streaks.
- [ ] Visual Skill Graph & Priority Queue progress view.

## Author

[Ophir Rephael Agami](https://github.com/OphirAgami) — a personal software engineering project inspired by my own English-learning experience.