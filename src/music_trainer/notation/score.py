from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ScoreEvent:
    slot: int
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScoreJson:
    clef: str
    key: str
    time_sig: str | None
    events: list[ScoreEvent] = field(default_factory=list)

    def place_note(self, slot: int, note: str, chord: bool = True) -> None:
        event = self._event_for_slot(slot)
        if chord:
            if note not in event.notes:
                event.notes.append(note)
        else:
            event.notes = [note]

    def delete_note(self, slot: int, note: str) -> None:
        event = self._event_for_slot(slot)
        event.notes = [n for n in event.notes if n != note]

    def clear(self) -> None:
        self.events.clear()

    def _event_for_slot(self, slot: int) -> ScoreEvent:
        for event in self.events:
            if event.slot == slot:
                return event
        event = ScoreEvent(slot=slot)
        self.events.append(event)
        self.events.sort(key=lambda e: e.slot)
        return event
