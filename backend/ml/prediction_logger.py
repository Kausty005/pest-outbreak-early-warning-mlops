"""Thread-safe JSONL logger for incoming prediction inputs.

Each crop prediction request is appended as one JSON line so that
the drift monitor can read them back as a "current" batch.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
_LOCK = threading.Lock()

DEFAULT_LOG_PATH = Path("logs/prediction_log.jsonl")


def log_prediction_input(
    inputs: dict[str, Any],
    log_path: str | Path = DEFAULT_LOG_PATH,
) -> None:
    """Append one prediction input record to the JSONL log (thread-safe)."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **{k: v for k, v in inputs.items()},
        "_logged_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with _LOCK:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to log prediction input: %s", exc)


def count_logged_predictions(log_path: str | Path = DEFAULT_LOG_PATH) -> int:
    """Return the number of prediction records logged so far."""
    path = Path(log_path)
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
