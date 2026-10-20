"""
src/utils/crop_catalog.py
─────────────────────────
Crop catalog import bridge for standalone utilities and scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.crop_catalog import (
    CropCatalog,
    CropNotFoundError,
    get_crop_catalog,
    DEFAULT_CATALOG_PATH,
)

__all__ = [
    "CropCatalog",
    "CropNotFoundError",
    "get_crop_catalog",
    "DEFAULT_CATALOG_PATH",
]
