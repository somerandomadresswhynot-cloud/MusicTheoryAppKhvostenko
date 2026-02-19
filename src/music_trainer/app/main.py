from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from music_trainer.content.manager import ContentManager


def run_headless(content_root: Path) -> int:
    manager = ContentManager(content_root)
    exercises = manager.load()
    print(f"Loaded {len(exercises)} exercise(s)")
    return 0


def run_gui(content_root: Path) -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    manager = ContentManager(content_root)
    manager.load()

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Music Theory Trainer")

    root = QWidget()
    layout = QHBoxLayout(root)

    sidebar = QListWidget()
    details = QTextEdit()
    details.setReadOnly(True)
    resync = QPushButton("Resync")

    def refresh() -> None:
        sidebar.clear()
        for exercise in manager.resync().values():
            item = QListWidgetItem(f"{exercise.domain}: {exercise.title}")
            item.setData(Qt.ItemDataRole.UserRole, exercise.exercise_id)
            sidebar.addItem(item)

    def on_selected() -> None:
        item = sidebar.currentItem()
        if item is None:
            return
        exercise_id = item.data(Qt.ItemDataRole.UserRole)
        exercise = manager.exercises[exercise_id]
        lines = [exercise.description, "", "Levels:"]
        for level in exercise.levels:
            keys = manager._keys_for_level(level)
            sample_item = manager.expand_level_items(exercise, level)[0]
            lines.append(f"- {level.label} ({len(keys)} keys, clef={level.range.get('clef')})")
            lines.append(f"  e.g. {sample_item.prompt}")
        details.setText("\n".join(lines))

    sidebar.currentItemChanged.connect(lambda *_: on_selected())
    resync.clicked.connect(refresh)

    left = QWidget()
    left_layout = QVBoxLayout(left)
    left_layout.addWidget(QLabel("Domains / Exercises"))
    left_layout.addWidget(sidebar)
    left_layout.addWidget(resync)

    layout.addWidget(left, 1)
    layout.addWidget(details, 2)

    window.setCentralWidget(root)
    refresh()
    window.resize(1000, 600)
    window.show()
    return app.exec()


if __name__ == "__main__":
    content_root = Path("content/exercises")
    if "--headless" in sys.argv:
        raise SystemExit(run_headless(content_root))
    try:
        raise SystemExit(run_gui(content_root))
    except ModuleNotFoundError:
        raise SystemExit(run_headless(content_root))
