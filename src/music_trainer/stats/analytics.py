from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(slots=True)
class LevelStats:
    due: int
    tracked: int
    avg_accuracy: float


class StatsService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def level_stats(self, exercise_id: str, level_id: str) -> LevelStats:
        due = self.conn.execute(
            "SELECT COUNT(*) c FROM cards WHERE exercise_id=? AND level_id=? AND due_at<=CURRENT_TIMESTAMP",
            (exercise_id, level_id),
        ).fetchone()["c"]
        tracked = self.conn.execute(
            "SELECT COUNT(*) c FROM cards WHERE exercise_id=? AND level_id=?",
            (exercise_id, level_id),
        ).fetchone()["c"]
        acc_row = self.conn.execute(
            "SELECT AVG(correct) avg_correct FROM attempts WHERE exercise_id=? AND level_id=?",
            (exercise_id, level_id),
        ).fetchone()
        avg_accuracy = float(acc_row["avg_correct"] or 0.0)
        return LevelStats(due=int(due), tracked=int(tracked), avg_accuracy=avg_accuracy)

    def key_coverage(self, exercise_id: str, level_id: str) -> dict[str, str]:
        rows = self.conn.execute(
            """
            SELECT item_id, AVG(correct) as acc
            FROM attempts
            WHERE exercise_id=? AND level_id=?
            GROUP BY item_id
            """,
            (exercise_id, level_id),
        ).fetchall()
        heat: dict[str, str] = {}
        for row in rows:
            item_id = row["item_id"]
            acc = float(row["acc"] or 0.0)
            if acc >= 0.85:
                heat[item_id] = "mastered"
            elif acc >= 0.5:
                heat[item_id] = "learning"
            else:
                heat[item_id] = "weak"
        return heat
