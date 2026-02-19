from pathlib import Path

from music_trainer.content.manager import ContentManager
from music_trainer.grading.pitch import grade_pitch_class_slots


def test_load_and_expand_keys() -> None:
    manager = ContentManager(Path("content/exercises"))
    exercises = manager.load()
    exercise = exercises["construct_functional_sequence_in_tonality"]
    level = exercise.levels[0]
    items = manager.expand_level_items(exercise, level)
    keys = [item.meta["key"] for item in items]
    assert set(keys) == {"C", "F", "G"}


def test_pitch_class_enharmonic_ok() -> None:
    result = grade_pitch_class_slots(expected_slots=[["C", "E", "G#"]], got_slots=[["B#", "E", "Ab"]])
    assert result.correct


def test_corrected_exercise_kinds_expand() -> None:
    manager = ContentManager(Path("content/exercises"))
    exercises = manager.load()

    chord_item = manager.expand_level_items(exercises["construct_structure_from_root"], exercises["construct_structure_from_root"].levels[0])[0]
    assert "Build a major triad" in chord_item.prompt

    sequence_item = manager.expand_level_items(
        exercises["construct_functional_sequence_in_tonality"], exercises["construct_functional_sequence_in_tonality"].levels[0]
    )[0]
    assert "Build progression I–IV–V" in sequence_item.prompt

    tension_item = manager.expand_level_items(exercises["resolve_tension_within_tonality"], exercises["resolve_tension_within_tonality"].levels[0])[0]
    assert "Resolve the tritone" in tension_item.prompt

    mode_item = manager.expand_level_items(
        exercises["construct_modal_scale_system_from_root"], exercises["construct_modal_scale_system_from_root"].levels[0]
    )[0]
    assert "Build Dorian mode" in mode_item.prompt

    harmonic_audiation = manager.expand_level_items(exercises["audiation_harmonic_structure"], exercises["audiation_harmonic_structure"].levels[0])[0]
    assert "Sing major 7th chord" in harmonic_audiation.prompt

    scalar_audiation = manager.expand_level_items(exercises["audiation_scalar_modal_system"], exercises["audiation_scalar_modal_system"].levels[0])[0]
    assert "Sing Lydian mode" in scalar_audiation.prompt
