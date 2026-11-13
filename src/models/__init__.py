"""
Models module for AgriAdapt AI fertilizer recommendation.
"""
from src.models.model import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGETS,
    FertilizerRecommendationModel,
)
from src.models.predict import (
    REQUIRED_FEATURES,
    VALID_CROPS,
    FertilizerPredictor,
    get_example_input,
    predict_fertilizer,
)

__all__ = [
    "CATEGORICAL_FEATURES",
    "NUMERIC_FEATURES",
    "REQUIRED_FEATURES",
    "TARGETS",
    "VALID_CROPS",
    "FertilizerPredictor",
    "FertilizerRecommendationModel",
    "get_example_input",
    "predict_fertilizer",
]
