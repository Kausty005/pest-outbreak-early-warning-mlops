"""
Models module for AgriAdapt AI fertilizer recommendation.
"""
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
    REQUIRED_FEATURES,
    VALID_CROPS,
)

__all__ = [
    "FertilizerRecommendationModel",
    "FertilizerPredictor",
    "predict_fertilizer",
    "get_example_input",
    "TARGETS",
    "NUMERIC_FEATURES",
    "CATEGORICAL_FEATURES",
    "REQUIRED_FEATURES",
    "VALID_CROPS",
]
