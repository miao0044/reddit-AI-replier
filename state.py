"""
Persistent state management for tracking replied comments and timestamps.
"""

import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path("state.json")


class State:
    """Manages persistent bot state across sessions."""

    def __init__(self, filepath: Path = STATE_FILE):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load state file: {e}")
        return {"last_run_time": 0.0, "replied_ids": []}

    def save(self) -> None:
        with open(self.filepath, "w") as f:
            json.dump(self._data, f, indent=2)
        logger.debug("State saved")

    @property
    def last_run_time(self) -> float:
        return self._data.get("last_run_time", 0.0)

    def update_run_time(self) -> None:
        self._data["last_run_time"] = time.time()
        self.save()

    def is_replied(self, comment_id: str) -> bool:
        return comment_id in self._data.get("replied_ids", [])

    def mark_replied(self, comment_id: str) -> None:
        replied = self._data.setdefault("replied_ids", [])
        if comment_id not in replied:
            replied.append(comment_id)
            # Keep only last 1000 IDs to prevent unbounded growth
            if len(replied) > 1000:
                self._data["replied_ids"] = replied[-1000:]
            self.save()
