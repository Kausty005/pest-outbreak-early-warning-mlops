"""
src/utils/logger.py
───────────────────
Self-contained logging setup for AgriAdapt AI standalone integration package.
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a module-level logger configured for both console and local log files.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s – %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler — wrap stdout in UTF-8 to prevent Windows cp1252 encoding issues
        if hasattr(sys.stdout, "buffer"):
            utf8_stdout = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
        else:
            utf8_stdout = sys.stdout

        ch = logging.StreamHandler(utf8_stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # File handler — write to logs/ inside package root if permissible
        try:
            log_dir = ROOT / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = log_dir / f"fertilizer_model_{today}.log"
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except Exception:
            # Fallback to console-only if directory creation or file writing fails
            pass

    logger.propagate = False
    return logger
