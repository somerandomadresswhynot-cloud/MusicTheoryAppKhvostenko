from pathlib import Path

from music_trainer.models import CardKey
from music_trainer.srs.scheduler import SRSScheduler


def test_srs_lifecycle(tmp_path: Path) -> None:
    scheduler = SRSScheduler(tmp_path / "srs.sqlite")
    key = CardKey("ex", "L1", "item=C")
    state = scheduler.get_or_create(key)
    assert state.reps == 0

    next_state = scheduler.review(key, "good")
    assert next_state.reps == 1
    assert next_state.interval_days >= 1
