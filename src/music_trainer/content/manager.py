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

PC_TO_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_PC = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}
CHORD_INTERVALS = {
    "major_triad": [0, 4, 7],
    "minor_triad": [0, 3, 7],
    "diminished_triad": [0, 3, 6],
    "augmented_triad": [0, 4, 8],
    "dominant_7th": [0, 4, 7, 10],
    "major_7th": [0, 4, 7, 11],
    "minor_7th": [0, 3, 7, 10],
}
MODE_INTERVALS = {
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
}
ROMAN_TO_DEGREE = {"I": 0, "ii": 1, "II": 1, "iii": 2, "III": 2, "IV": 3, "V": 4, "vi": 5, "VI": 5, "vii": 6, "VII": 6}
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]


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
        kind = exercise.generator.get("kind", "construct_functional_sequence")

        if kind in {"roman_progression", "construct_functional_sequence"}:
            return [self._progression_item(exercise, level, key) for key in keys]
        if kind in {"chord_from_note", "construct_structure_from_root"}:
            return [self._chord_from_note_item(exercise, level, key) for key in keys]
        if kind in {"resolve_tritone", "resolve_tension"}:
            return [self._resolve_tritone_item(exercise, level, key) for key in keys]
        if kind in {"mode_from_note", "construct_modal_system"}:
            return [self._mode_item(exercise, level, key) for key in keys]
        if kind in {"self_grade_sing", "audiation_harmonic_structure", "audiation_scalar_modal_system"}:
            return [self._self_grade_item(exercise, level, key) for key in keys]
        raise ContentError(f"Unsupported generator kind: {kind}")

    def _progression_item(self, exercise: ExerciseDefinition, level: LevelDefinition, key: str) -> ItemDefinition:
        progression = exercise.generator.get("params", {}).get("progressions", [["I", "IV", "V"]])[0]
        slots = [self._triad_for_degree(key, degree) for degree in progression]
        display = "–".join(progression)
        return ItemDefinition(
            item_id=f"functional_sequence_key={key}_pattern={'-'.join(progression)}",
            exercise_id=exercise.exercise_id,
            level_id=level.level_id,
            meta={"key": key, "progression": progression},
            expected={"score_json": {"key": key, "slots": slots}},
            prompt=f"Build progression {display} in {key} major",
        )

    def _chord_from_note_item(self, exercise: ExerciseDefinition, level: LevelDefinition, key: str) -> ItemDefinition:
        params = exercise.generator.get("params", {})
        structure_type = params.get("structure_type", params.get("chord_type", "major_triad"))
        direction = params.get("direction", "up")
        intervals = CHORD_INTERVALS[structure_type]
        if direction == "down":
            intervals = [0] + [-(12 - i) if i != 0 else 0 for i in intervals[1:]]
        notes = [self._transpose(key, i) for i in intervals]
        structure_label = structure_type.replace("_", " ")
        return ItemDefinition(
            item_id=f"structure_from_root_note={key}_type={structure_type}_dir={direction}",
            exercise_id=exercise.exercise_id,
            level_id=level.level_id,
            meta={"note": key, "structure_type": structure_type, "direction": direction},
            expected={"score_json": {"key": key, "slots": [notes]}},
            prompt=f"Build a {structure_label} from {key} {direction}",
        )

    def _resolve_tritone_item(self, exercise: ExerciseDefinition, level: LevelDefinition, key: str) -> ItemDefinition:
        tonic_pc = NOTE_TO_PC[key]
        fourth = PC_TO_SHARP[(tonic_pc + 5) % 12]
        leading = PC_TO_SHARP[(tonic_pc + 11) % 12]
        resolved = [PC_TO_SHARP[(tonic_pc + 4) % 12], PC_TO_SHARP[tonic_pc]]
        return ItemDefinition(
            item_id=f"resolve_tension_key={key}",
            exercise_id=exercise.exercise_id,
            level_id=level.level_id,
            meta={"key": key, "tritone": [fourth, leading]},
            expected={"score_json": {"key": key, "slots": [[fourth, leading], resolved]}},
            prompt=f"Resolve the tritone in {key} major",
        )

    def _mode_item(self, exercise: ExerciseDefinition, level: LevelDefinition, key: str) -> ItemDefinition:
        params = exercise.generator.get("params", {})
        mode = params.get("mode", "dorian")
        direction = params.get("direction", "up")
        intervals = MODE_INTERVALS[mode]
        if direction == "down":
            intervals = [0] + [-i for i in intervals[1:]]
        notes = [self._transpose(key, i) for i in intervals]
        return ItemDefinition(
            item_id=f"modal_system_note={key}_mode={mode}_dir={direction}",
            exercise_id=exercise.exercise_id,
            level_id=level.level_id,
            meta={"note": key, "mode": mode, "direction": direction},
            expected={"score_json": {"key": key, "slots": [[n] for n in notes]}},
            prompt=f"Build {mode.capitalize()} mode {direction} from {key}",
        )

    def _self_grade_item(self, exercise: ExerciseDefinition, level: LevelDefinition, key: str) -> ItemDefinition:
        params = exercise.generator.get("params", {})
        template = params.get("template", "Sing exercise from {note}")
        return ItemDefinition(
            item_id=f"self_grade_note={key}",
            exercise_id=exercise.exercise_id,
            level_id=level.level_id,
            meta={"note": key, "self_grade_map": params.get("grade_map", {})},
            expected={"score_json": {"key": key, "slots": []}},
            prompt=template.format(note=key),
        )

    def _triad_for_degree(self, key: str, degree: str) -> list[str]:
        if degree not in ROMAN_TO_DEGREE:
            raise ContentError(f"Unsupported roman degree: {degree}")
        scale_degree = ROMAN_TO_DEGREE[degree]
        tonic_pc = NOTE_TO_PC[key]
        root_pc = (tonic_pc + MAJOR_SCALE_INTERVALS[scale_degree]) % 12
        third_pc = (tonic_pc + MAJOR_SCALE_INTERVALS[(scale_degree + 2) % 7]) % 12
        fifth_pc = (tonic_pc + MAJOR_SCALE_INTERVALS[(scale_degree + 4) % 7]) % 12
        return [PC_TO_SHARP[root_pc], PC_TO_SHARP[third_pc], PC_TO_SHARP[fifth_pc]]

    def _transpose(self, note: str, semitones: int) -> str:
        return PC_TO_SHARP[(NOTE_TO_PC[note] + semitones) % 12]

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
