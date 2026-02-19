from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LevelDefinition:
    level_id: str
    label: str
    key_scope: dict[str, Any]
    range: dict[str, Any]
    time_sig: str | None = None
    instrument_scope: dict[str, Any] = field(default_factory=dict)
    modes: dict[str, Any] = field(default_factory=dict)
    grading: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExerciseDefinition:
    schema_version: int
    exercise_id: str
    title: str
    domain: str
    type: str
    description: str
    levels: list[LevelDefinition]
    generator: dict[str, Any]
    ui: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ItemDefinition:
    item_id: str
    exercise_id: str
    level_id: str
    meta: dict[str, Any]
    expected: dict[str, Any]
    prompt: str


@dataclass(slots=True)
class CardKey:
    exercise_id: str
    level_id: str
    item_id: str
    instrument_id: str = "default"
    range_id: str = "default"
    mode_id: str = "default"

    def as_tuple(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.exercise_id,
            self.level_id,
            self.item_id,
            self.instrument_id,
            self.range_id,
            self.mode_id,
        )
