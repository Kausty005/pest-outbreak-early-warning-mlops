"""Shared, sklearn-compatible transformations for training and inference."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .data_validation import FEATURE_COLUMNS

ENGINEERED_NUMERIC_COLUMNS = [
    "npk_total",
    "nitrogen_phosphorus_ratio",
    "nitrogen_potassium_ratio",
    "phosphorus_potassium_ratio",
    "temperature_humidity_interaction",
]
ENGINEERED_CATEGORICAL_COLUMNS = ["ph_category", "rainfall_category"]


@dataclass(frozen=True)
class FeatureConfig:
    enabled: bool = False
    acidic_threshold: float = 6.5
    alkaline_threshold: float = 7.5
    low_rainfall_threshold: float = 100.0
    high_rainfall_threshold: float = 200.0
    zero_denominator_value: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def _frame_from_input(X: pd.DataFrame | np.ndarray | Iterable) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        missing = [column for column in FEATURE_COLUMNS if column not in X.columns]
        if missing:
            raise ValueError(f"Input is missing required features: {missing}")
        return X.loc[:, FEATURE_COLUMNS].copy()
    array = np.asarray(X)
    if array.ndim != 2 or array.shape[1] != len(FEATURE_COLUMNS):
        raise ValueError(f"Expected a 2-D array with {len(FEATURE_COLUMNS)} features in {FEATURE_COLUMNS} order")
    return pd.DataFrame(array, columns=FEATURE_COLUMNS)


class CropFeatureBuilder(BaseEstimator, TransformerMixin):
    """Adds deterministic domain features; it learns no state from the data."""

    def __init__(
        self,
        enabled: bool = False,
        acidic_threshold: float = 6.5,
        alkaline_threshold: float = 7.5,
        low_rainfall_threshold: float = 100.0,
        high_rainfall_threshold: float = 200.0,
        zero_denominator_value: float = 0.0,
    ) -> None:
        self.enabled = enabled
        self.acidic_threshold = acidic_threshold
        self.alkaline_threshold = alkaline_threshold
        self.low_rainfall_threshold = low_rainfall_threshold
        self.high_rainfall_threshold = high_rainfall_threshold
        self.zero_denominator_value = zero_denominator_value

    def fit(self, X, y=None):
        _frame_from_input(X)
        if self.acidic_threshold >= self.alkaline_threshold:
            raise ValueError("acidic_threshold must be below alkaline_threshold")
        if self.low_rainfall_threshold >= self.high_rainfall_threshold:
            raise ValueError("low_rainfall_threshold must be below high_rainfall_threshold")
        return self

    def transform(self, X):
        frame = _frame_from_input(X)
        for column in FEATURE_COLUMNS:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        values = frame[FEATURE_COLUMNS].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("All model inputs must be finite numeric values")
        if not self.enabled:
            return frame

        n, p, k = (frame[column].to_numpy(dtype=float) for column in ("N", "P", "K"))
        safe_divide = lambda numerator, denominator: np.divide(
            numerator,
            denominator,
            out=np.full(numerator.shape, self.zero_denominator_value, dtype=float),
            where=denominator != 0,
        )
        frame["npk_total"] = n + p + k
        frame["nitrogen_phosphorus_ratio"] = safe_divide(n, p)
        frame["nitrogen_potassium_ratio"] = safe_divide(n, k)
        frame["phosphorus_potassium_ratio"] = safe_divide(p, k)
        frame["temperature_humidity_interaction"] = frame["temperature"] * frame["humidity"] / 100.0
        frame["ph_category"] = np.select(
            [frame["ph"] < self.acidic_threshold, frame["ph"] <= self.alkaline_threshold],
            ["acidic", "near_neutral"],
            default="alkaline",
        )
        frame["rainfall_category"] = np.select(
            [frame["rainfall"] < self.low_rainfall_threshold, frame["rainfall"] <= self.high_rainfall_threshold],
            ["low", "medium"],
            default="high",
        )
        return frame

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.output_columns)

    @property
    def output_columns(self) -> list[str]:
        if not self.enabled:
            return list(FEATURE_COLUMNS)
        return list(FEATURE_COLUMNS) + ENGINEERED_NUMERIC_COLUMNS + ENGINEERED_CATEGORICAL_COLUMNS


def make_preprocessor(config: FeatureConfig) -> ColumnTransformer:
    numeric_columns = list(FEATURE_COLUMNS)
    if config.enabled:
        numeric_columns += ENGINEERED_NUMERIC_COLUMNS
    transformers = [("numeric", "passthrough", numeric_columns)]
    if config.enabled:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        except TypeError:  # scikit-learn < 1.2
            encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        transformers.append(("categories", encoder, ENGINEERED_CATEGORICAL_COLUMNS))
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def make_model_pipeline(estimator, config: FeatureConfig) -> Pipeline:
    builder = CropFeatureBuilder(**config.to_dict())
    return Pipeline(
        steps=[
            ("features", builder),
            ("preprocess", make_preprocessor(config)),
            ("model", estimator),
        ]
    )
