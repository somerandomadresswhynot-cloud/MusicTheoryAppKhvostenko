from pathlib import Path

from music_trainer.content.manager import ContentManager
from music_trainer.grading.pitch import grade_pitch_class_slots


def test_load_and_expand_keys() -> None:
    manager = ContentManager(Path("content/exercises"))
    exercises = manager.load()
    exercise = exercises["progression_I_IV_V"]
    level = exercise.levels[0]
    items = manager.expand_level_items(exercise, level)
    keys = [item.meta["key"] for item in items]
    assert set(keys) == {"C", "F", "G"}


def test_pitch_class_enharmonic_ok() -> None:
    result = grade_pitch_class_slots(expected_slots=[["C", "E", "G#"]], got_slots=[["B#", "E", "Ab"]])
    assert result.correct
