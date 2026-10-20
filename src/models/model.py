"""
src/models/model.py
───────────────────
Core model class and prediction wrapper for AgriAdapt AI fertilizer recommendations.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor

TARGETS = ["target_n_kg_ha", "target_p2o5_kg_ha", "target_k2o_kg_ha"]

NUMERIC_FEATURES = [
    "nitrogen__nutrient_index", "nitrogen__pct_low", "nitrogen__pct_medium", "nitrogen__pct_high",
    "phosphorus__nutrient_index", "phosphorus__pct_low", "phosphorus__pct_medium", "phosphorus__pct_high",
    "potassium__nutrient_index", "potassium__pct_low", "potassium__pct_medium", "potassium__pct_high",
    "soil_ph__nutrient_index", "soil_ph__pct_low", "soil_ph__pct_medium", "soil_ph__pct_high",
    "organic_carbon__nutrient_index", "organic_carbon__pct_low", "organic_carbon__pct_medium", "organic_carbon__pct_high",
    "electrical_conductivity__nutrient_index", "electrical_conductivity__pct_low", "electrical_conductivity__pct_medium", "electrical_conductivity__pct_high",
    "boron__nutrient_index", "copper__nutrient_index", "iron__nutrient_index",
    "manganese__nutrient_index", "sulphur__nutrient_index", "zinc__nutrient_index",
    "nitrogen__total_samples",
]

CATEGORICAL_FEATURES = ["crop", "crop_season", "state_name"]


class FertilizerRecommendationModel:
    """
    Production container for trained AgriAdapt AI models and preprocessing.
    """
    def __init__(
        self,
        preprocessor: ColumnTransformer,
        models: dict[str, RandomForestRegressor],
        crop_means: dict[str, dict[str, float]],
        global_means: dict[str, float],
        feature_names: list[str],
        metadata: dict[str, Any],
    ):
        self.preprocessor = preprocessor
        self.models = models
        self.crop_means = crop_means
        self.global_means = global_means
        self.feature_names = feature_names
        self.metadata = metadata

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict recommended N, P2O5, K2O in kg/ha for input DataFrame.
        """
        X_trans = self.preprocessor.transform(df)
        preds = {}
        for target_name, model in self.models.items():
            col_name = target_name.replace("target_", "pred_")
            preds[col_name] = model.predict(X_trans)
        return pd.DataFrame(preds, index=df.index)

    def predict_baseline_crop(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict using Crop-Stratified Mean baseline.
        """
        preds = {}
        for target_name in TARGETS:
            col_name = target_name.replace("target_", "pred_baseline_crop_")
            means = self.crop_means[target_name]
            default_val = self.global_means[target_name]
            preds[col_name] = df["crop"].map(means).fillna(default_val).values
        return pd.DataFrame(preds, index=df.index)

    def predict_baseline_global(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict using Global Mean baseline.
        """
        preds = {}
        for target_name in TARGETS:
            col_name = target_name.replace("target_", "pred_baseline_global_")
            preds[col_name] = np.full(len(df), self.global_means[target_name])
        return pd.DataFrame(preds, index=df.index)
