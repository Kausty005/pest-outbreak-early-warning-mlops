"""
backend/ml/fertilizer.py
─────────────────────────
Fertilizer prediction engine and model wrapper for AgriAdapt AI MLOps pipeline.
Integrates the Indian Soil Health Card + ICAR-IISS general fertilizer recommendation ensemble.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is in sys.path so pickle unpickling of src.models.model succeeds
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGETS,
    FertilizerRecommendationModel,
)
from src.models.predict import (  # noqa: E402
    DEFAULT_MODEL_PATH,
    REQUIRED_FEATURES,
    SCHEMA_PATH,
    VALID_CROPS,
    FertilizerPredictor,
    get_example_input,
    predict_fertilizer,
)

__all__ = [
    "CATEGORICAL_FEATURES",
    "DEFAULT_MODEL_PATH",
    "NUMERIC_FEATURES",
    "REQUIRED_FEATURES",
    "SCHEMA_PATH",
    "TARGETS",
    "VALID_CROPS",
    "FertilizerPredictor",
    "FertilizerRecommendationModel",
    "get_example_input",
    "predict_fertilizer",
]
