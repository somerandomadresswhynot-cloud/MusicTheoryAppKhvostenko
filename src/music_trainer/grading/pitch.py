from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(slots=True)
class SlotDiff:
    index: int
    expected: set[int]
    got: set[int]
    matched: bool


@dataclass(slots=True)
class GradeResult:
    correct: bool
    slot_diffs: list[SlotDiff]



def to_pitch_class(note: str) -> int:
    pc = NOTE_TO_PC.get(note)
    if pc is None:
        raise ValueError(f"Unsupported note spelling: {note}")
    return pc


def grade_pitch_class_slots(expected_slots: list[list[str]], got_slots: list[list[str]]) -> GradeResult:
    max_len = max(len(expected_slots), len(got_slots))
    diffs: list[SlotDiff] = []
    for idx in range(max_len):
        expected = {to_pitch_class(n) for n in expected_slots[idx]} if idx < len(expected_slots) else set()
        got = {to_pitch_class(n) for n in got_slots[idx]} if idx < len(got_slots) else set()
        diffs.append(SlotDiff(index=idx, expected=expected, got=got, matched=expected == got))
    return GradeResult(correct=all(d.matched for d in diffs), slot_diffs=diffs)
