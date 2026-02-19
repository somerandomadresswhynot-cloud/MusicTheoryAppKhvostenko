from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlaybackRequest:
    notes: list[str]
    instrument: str = "piano"
    tempo: int = 90


class AudioEngine:
    """MVP placeholder for sample/synth playback integration."""

    def play_reference(self, note: str, instrument: str = "piano") -> PlaybackRequest:
        return PlaybackRequest(notes=[note], instrument=instrument)

    def play_score(self, notes: list[str], instrument: str = "piano") -> PlaybackRequest:
        return PlaybackRequest(notes=notes, instrument=instrument)
