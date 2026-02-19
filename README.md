# Music Theory Trainer (MVP skeleton)

Cross-platform desktop app architecture for structured music exercises with SRS scheduling.

## Implemented MVP foundations

- Modular content loader for JSON exercises (`content/exercises/**/exercise.json`)
- Level expansion by key coverage (`max_accidentals`)
- Internal score JSON model with note/chord edit operations (place/select/delete/clear primitives)
- Pitch-class-set grader for slot/chord matching
- SQLite-backed SRS scheduler with Again/Hard/Good/Easy grades
- Stats service with due/tracked/accuracy and key coverage classification
- PySide6 desktop shell (with headless fallback if Qt is unavailable)

## Run

```bash
python -m music_trainer.app.main --headless
```

or with GUI (if PySide6 installed):

```bash
python -m music_trainer.app.main
```

## Notes

- Notation renderer/editor embedding (OSMD/Smoosic via QtWebEngine) is represented as architecture stubs in this MVP skeleton.
- Audio playback is exposed through a minimal API placeholder for future sampler/synth integration.
