from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from music_trainer.models import ExerciseDefinition, ItemDefinition, LevelDefinition

MAJOR_KEYS_BY_ACCIDENTALS = [
    (0, "C"),
    (1, "G"),
    (2, "D"),
    (3, "A"),
    (4, "E"),
    (5, "B"),
    (6, "F#"),
    (7, "C#"),
    (-1, "F"),
    (-2, "Bb"),
    (-3, "Eb"),
    (-4, "Ab"),
    (-5, "Db"),
    (-6, "Gb"),
    (-7, "Cb"),
]


class ContentError(ValueError):
    pass


class ContentManager:
    def __init__(self, content_root: Path) -> None:
        self.content_root = content_root
        self.exercises: dict[str, ExerciseDefinition] = {}

    def load(self) -> dict[str, ExerciseDefinition]:
        loaded: dict[str, ExerciseDefinition] = {}
        for path in self.content_root.rglob("exercise.json"):
            exercise = self._parse_exercise(path)
            loaded[exercise.exercise_id] = exercise
        self.exercises = loaded
        return loaded

    def resync(self) -> dict[str, ExerciseDefinition]:
        return self.load()

    def expand_level_items(self, exercise: ExerciseDefinition, level: LevelDefinition) -> list[ItemDefinition]:
        keys = self._keys_for_level(level)
        return [
            ItemDefinition(
                item_id=f"{exercise.generator.get('kind', 'item')}_key={key}",
                exercise_id=exercise.exercise_id,
                level_id=level.level_id,
                meta={"key": key},
                expected={"score_json": {"notes": [], "key": key}},
                prompt=f"Key: {key} major. {exercise.title}",
            )
            for key in keys
        ]

    def _keys_for_level(self, level: LevelDefinition) -> list[str]:
        system = level.key_scope.get("system", "major")
        if system != "major":
            raise ContentError(f"Only major key system is supported in MVP, got {system}")
        max_acc = int(level.key_scope.get("max_accidentals", 0))
        keys = [k for acc, k in MAJOR_KEYS_BY_ACCIDENTALS if abs(acc) <= max_acc]
        return sorted(set(keys), key=keys.index)

    def _parse_exercise(self, path: Path) -> ExerciseDefinition:
        raw = json.loads(path.read_text(encoding="utf-8"))
        required = ["schema_version", "exercise_id", "title", "domain", "type", "description", "levels", "generator"]
        for field_name in required:
            if field_name not in raw:
                raise ContentError(f"{path}: missing required field '{field_name}'")

        levels: list[LevelDefinition] = []
        for idx, level in enumerate(raw["levels"]):
            try:
                levels.append(
                    LevelDefinition(
                        level_id=level["level_id"],
                        label=level["label"],
                        key_scope=level["key_scope"],
                        range=level["range"],
                        time_sig=level.get("time_sig"),
                        instrument_scope=level.get("instrument_scope", {}),
                        modes=level.get("modes", {}),
                        grading=level.get("grading", {}),
                    )
                )
            except KeyError as exc:
                raise ContentError(f"{path}: levels[{idx}] missing field {exc}") from exc

        return ExerciseDefinition(
            schema_version=int(raw["schema_version"]),
            exercise_id=raw["exercise_id"],
            title=raw["title"],
            domain=raw["domain"],
            type=raw["type"],
            description=raw["description"],
            levels=levels,
            generator=raw["generator"],
            ui=raw.get("ui", {}),
        )

    @staticmethod
    def dump_normalized(exercise: ExerciseDefinition) -> dict:
        return asdict(exercise)
