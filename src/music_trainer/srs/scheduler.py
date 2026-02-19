from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from music_trainer.models import CardKey

GRADE_MULTIPLIER = {
    "again": 0.0,
    "hard": 0.7,
    "good": 1.0,
    "easy": 1.5,
}


@dataclass(slots=True)
class CardState:
    key: CardKey
    due_at: datetime
    interval_days: float
    ease: float
    reps: int


class SRSScheduler:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cards (
                exercise_id TEXT,
                level_id TEXT,
                item_id TEXT,
                instrument_id TEXT,
                range_id TEXT,
                mode_id TEXT,
                due_at TEXT,
                interval_days REAL,
                ease REAL,
                reps INTEGER,
                PRIMARY KEY(exercise_id, level_id, item_id, instrument_id, range_id, mode_id)
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                exercise_id TEXT,
                level_id TEXT,
                item_id TEXT,
                instrument_id TEXT,
                range_id TEXT,
                mode_id TEXT,
                grade TEXT,
                correct INTEGER,
                payload_json TEXT
            );
            """
        )
        self.conn.commit()

    def get_or_create(self, key: CardKey) -> CardState:
        row = self.conn.execute(
            """
            SELECT * FROM cards WHERE exercise_id=? AND level_id=? AND item_id=?
            AND instrument_id=? AND range_id=? AND mode_id=?
            """,
            key.as_tuple(),
        ).fetchone()
        now = datetime.now(timezone.utc)
        if row is None:
            state = CardState(key=key, due_at=now, interval_days=0.0, ease=2.5, reps=0)
            self._upsert(state)
            return state
        return CardState(
            key=key,
            due_at=datetime.fromisoformat(row["due_at"]),
            interval_days=float(row["interval_days"]),
            ease=float(row["ease"]),
            reps=int(row["reps"]),
        )

    def review(self, key: CardKey, grade: str) -> CardState:
        grade = grade.lower()
        if grade not in GRADE_MULTIPLIER:
            raise ValueError(f"Unsupported grade: {grade}")
        state = self.get_or_create(key)
        if grade == "again":
            state.interval_days = 1 / 24
            state.reps = 0
            state.ease = max(1.3, state.ease - 0.2)
        else:
            base = 1.0 if state.reps == 0 else max(1.0, state.interval_days * state.ease)
            state.interval_days = base * GRADE_MULTIPLIER[grade]
            state.reps += 1
            if grade == "easy":
                state.ease += 0.15
            elif grade == "hard":
                state.ease = max(1.3, state.ease - 0.05)
        state.due_at = datetime.now(timezone.utc) + timedelta(days=state.interval_days)
        self._upsert(state)
        return state

    def due_count(self, exercise_id: str, level_id: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) c FROM cards WHERE exercise_id=? AND level_id=? AND due_at<=?",
            (exercise_id, level_id, now),
        ).fetchone()
        return int(row["c"])

    def _upsert(self, state: CardState) -> None:
        self.conn.execute(
            """
            INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(exercise_id, level_id, item_id, instrument_id, range_id, mode_id)
            DO UPDATE SET due_at=excluded.due_at, interval_days=excluded.interval_days,
            ease=excluded.ease, reps=excluded.reps
            """,
            (*state.key.as_tuple(), state.due_at.isoformat(), state.interval_days, state.ease, state.reps),
        )
        self.conn.commit()
