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

from src.models.model import (
    FertilizerRecommendationModel,
    TARGETS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from src.models.predict import (
    FertilizerPredictor,
    predict_fertilizer,
    get_example_input,
    VALID_CROPS,
    REQUIRED_FEATURES,
    DEFAULT_MODEL_PATH,
    SCHEMA_PATH,
)

__all__ = [
    "FertilizerRecommendationModel",
    "FertilizerPredictor",
    "predict_fertilizer",
    "get_example_input",
    "VALID_CROPS",
    "REQUIRED_FEATURES",
    "NUMERIC_FEATURES",
    "CATEGORICAL_FEATURES",
    "TARGETS",
    "DEFAULT_MODEL_PATH",
    "SCHEMA_PATH",
]
