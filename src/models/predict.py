"""
src/models/predict.py
─────────────────────
Production inference module for AgriAdapt AI Fertilizer Recommendation Model.

Capabilities:
  1. Loads trained model container (models/fertilizer_model.joblib).
  2. Accepts inputs as a Python dictionary, list of dicts, or pandas DataFrame.
  3. Validates required features, data types, and physical bounds.
  4. Rejects invalid, out-of-bounds, or missing required features with clear errors.
  5. Returns predictions with nutrient names, chemical forms, and units (kg/ha).
  6. Avoids silently filling missing required inputs with arbitrary values.
  7. Includes working example prediction using valid test holdout inputs.

Usage:
  python -m src.models.predict
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

from src.models.model import (
    FertilizerRecommendationModel,
    TARGETS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from src.utils.logger import get_logger

log = get_logger(__name__)

DEFAULT_MODEL_PATH = ROOT / "backend" / "artifacts" / "fertilizer_model.joblib"
if not DEFAULT_MODEL_PATH.exists():
    DEFAULT_MODEL_PATH = ROOT / "models" / "fertilizer_model.joblib"

SCHEMA_PATH = ROOT / "backend" / "artifacts" / "fertilizer_feature_schema.json"
if not SCHEMA_PATH.exists():
    SCHEMA_PATH = ROOT / "models" / "fertilizer_feature_schema.json"

VALID_CROPS = {
    "Rice",
    "Wheat",
    "Sugarcane",
    "Kharif Maize",
    "Rabi Maize",
    "Kharif Rice",
    "Rice-Rabi",
}

# Core required features that MUST be provided by the caller
REQUIRED_FEATURES = [
    "crop",
    "state_name",
    "nitrogen__nutrient_index",
    "phosphorus__nutrient_index",
    "potassium__nutrient_index",
    "soil_ph__nutrient_index",
    "organic_carbon__nutrient_index",
]


class FertilizerPredictor:
    """
    Production prediction engine for AgriAdapt AI fertilizer recommendations.
    """

    def __init__(self, model_path: Union[str, Path] = DEFAULT_MODEL_PATH):
        self.model_path = Path(model_path)
        self.model: FertilizerRecommendationModel = self._load_model()
        self.feature_names = self.model.feature_names

    def _load_model(self) -> FertilizerRecommendationModel:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                "Train the model first using: python -m src.models.train"
            )
        try:
            model = joblib.load(self.model_path)
            log.info("Loaded fertilizer model from %s", self.model_path)
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.model_path}: {e}") from e

    @staticmethod
    def _derive_crop_season(crop: str) -> str:
        c = str(crop).strip().lower()
        if "kharif" in c or c == "rice":
            return "Kharif"
        elif "rabi" in c or c == "wheat":
            return "Rabi"
        elif "sugarcane" in c:
            return "Annual"
        return "Kharif"

    def validate_and_prepare_input(
        self, input_data: Union[dict[str, Any], list[dict[str, Any]], pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Validate input format, check required features, verify data types and physical bounds,
        and prepare a structured DataFrame ready for model preprocessing.
        """
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
            is_single = True
        elif isinstance(input_data, list):
            if len(input_data) == 0:
                raise ValueError("Input list is empty. Provide at least one record.")
            df = pd.DataFrame(input_data)
            is_single = False
        elif isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
            is_single = len(df) == 1
        else:
            raise TypeError(
                f"Unsupported input type '{type(input_data).__name__}'. "
                "Expected dict, list of dicts, or pandas DataFrame."
            )

        # ── 1. Check Required Features Presence ─────────────────────────────
        missing_required = [f for f in REQUIRED_FEATURES if f not in df.columns]
        if missing_required:
            raise ValueError(
                f"Missing required input features: {missing_required}. "
                f"All of the following must be provided: {REQUIRED_FEATURES}"
            )

        # ── 2. Validate Categorical Values ──────────────────────────────────
        for idx, row in df.iterrows():
            crop_val = row["crop"]
            if not isinstance(crop_val, str) or not crop_val.strip():
                raise ValueError(f"Record {idx}: 'crop' must be a non-empty string, got: {crop_val!r}")
            crop_clean = crop_val.strip()
            if crop_clean not in VALID_CROPS:
                raise ValueError(
                    f"Record {idx}: Unrecognized crop '{crop_clean}'. "
                    f"Must be one of: {sorted(VALID_CROPS)}"
                )

            state_val = row["state_name"]
            if not isinstance(state_val, str) or not state_val.strip():
                raise ValueError(f"Record {idx}: 'state_name' must be a non-empty string, got: {state_val!r}")

        # ── 3. Validate Numeric Values & Physical Bounds ─────────────────────
        # Nutrient Index bounds: [1.0, 3.0]
        ni_cols = [c for c in df.columns if c.endswith("__nutrient_index")]
        for col in ni_cols:
            for idx in df.index:
                val = df.at[idx, col]
                if pd.isna(val):
                    if col in REQUIRED_FEATURES:
                        raise ValueError(f"Record {idx}: Required nutrient index '{col}' cannot be null or NaN.")
                    continue
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    raise TypeError(f"Record {idx}: '{col}' must be numeric, got {type(val).__name__} ({val!r})")

                # Allow modest tolerance [0.8, 3.2] for laboratory measurement variance
                if num_val < 0.8 or num_val > 3.2:
                    raise ValueError(
                        f"Record {idx}: '{col}' value {num_val} is physically invalid. "
                        "Ramamoorthy & Bajaj Nutrient Index must be within [1.0, 3.0]."
                    )
                df.at[idx, col] = num_val

        # Percentage bounds: [0.0, 100.0]
        pct_cols = [c for c in df.columns if "__pct_" in c]
        for col in pct_cols:
            for idx in df.index:
                val = df.at[idx, col]
                if pd.isna(val):
                    continue
                try:
                    num_val = float(val)
                except (ValueError, TypeError):
                    raise TypeError(f"Record {idx}: '{col}' must be numeric, got {type(val).__name__} ({val!r})")
                if num_val < 0.0 or num_val > 100.0:
                    raise ValueError(
                        f"Record {idx}: '{col}' value {num_val} is invalid. "
                        "Percentage values must be within [0.0, 100.0]."
                    )
                df.at[idx, col] = num_val

        # ── 4. Auto-Infer crop_season if Missing ─────────────────────────────
        if "crop_season" not in df.columns:
            df["crop_season"] = df["crop"].apply(self._derive_crop_season)
        else:
            df["crop_season"] = df["crop_season"].fillna(df["crop"].apply(self._derive_crop_season))

        # ── 5. Ensure All Model Numeric Columns Exist ────────────────────────
        # Fill optional unprovided soil features with NaN (which the fitted SimpleImputer handles empirically)
        for num_f in NUMERIC_FEATURES:
            if num_f not in df.columns:
                df[num_f] = np.nan

        return df

    def predict(
        self,
        input_data: Union[dict[str, Any], list[dict[str, Any]], pd.DataFrame],
        return_format: str = "auto",
    ) -> Union[dict[str, Any], list[dict[str, Any]], pd.DataFrame]:
        """
        Execute prediction and return recommendations with nutrient names and units.

        Parameters
        ----------
        input_data : dict, list of dicts, or pandas DataFrame.
        return_format : 'auto', 'dict', or 'dataframe'.
            If 'auto', returns dict for single dict input, DataFrame for DataFrame input.

        Returns
        -------
        Dictionary or DataFrame containing:
          - recommended_n_kg_ha: Recommended Nitrogen (N) in kg/ha
          - recommended_p2o5_kg_ha: Recommended Phosphorus (P2O5) in kg/ha
          - recommended_k2o_kg_ha: Recommended Potassium (K2O) in kg/ha
          - units and agronomic metadata annotations.
        """
        is_single_dict = isinstance(input_data, dict)
        df_prepared = self.validate_and_prepare_input(input_data)

        raw_preds = self.model.predict(df_prepared)

        df_out = pd.DataFrame({
            "crop": df_prepared["crop"],
            "state_name": df_prepared["state_name"],
            "recommended_n_kg_ha": np.round(raw_preds["pred_n_kg_ha"], 2),
            "recommended_p2o5_kg_ha": np.round(raw_preds["pred_p2o5_kg_ha"], 2),
            "recommended_k2o_kg_ha": np.round(raw_preds["pred_k2o_kg_ha"], 2),
            "unit": "kg/ha",
        }, index=df_prepared.index)

        if return_format == "dict" or (return_format == "auto" and is_single_dict):
            row = df_out.iloc[0]
            return {
                "crop": row["crop"],
                "state_name": row["state_name"],
                "recommendations": {
                    "nitrogen": {
                        "value": float(row["recommended_n_kg_ha"]),
                        "unit": "kg/ha",
                        "chemical_form": "N (elemental)",
                    },
                    "phosphorus": {
                        "value": float(row["recommended_p2o5_kg_ha"]),
                        "unit": "kg/ha",
                        "chemical_form": "P2O5 (phosphate)",
                    },
                    "potassium": {
                        "value": float(row["recommended_k2o_kg_ha"]),
                        "unit": "kg/ha",
                        "chemical_form": "K2O (potash)",
                    },
                },
                "fertilizer_commercial_equivalent_approx": {
                    "urea_46_pct_n_kg_ha": round(float(row["recommended_n_kg_ha"]) / 0.46, 1),
                    "dap_46_pct_p2o5_kg_ha": round(float(row["recommended_p2o5_kg_ha"]) / 0.46, 1),
                    "mop_60_pct_k2o_kg_ha": round(float(row["recommended_k2o_kg_ha"]) / 0.60, 1),
                },
                "disclaimer": (
                    "Baseline general recommendation for district agroclimatic zone. "
                    "Adjust +/- 25% based on field-specific soil test rating and organic manure."
                ),
            }

        if return_format == "dict" and not is_single_dict:
            return df_out.to_dict(orient="records")

        return df_out


def get_example_input() -> dict[str, Any]:
    """Return a verified example input based on Pune district soil and Rice cultivation."""
    return {
        "crop": "Rice",
        "state_name": "Maharashtra",
        "crop_season": "Kharif",
        "nitrogen__nutrient_index": 1.34,
        "nitrogen__pct_low": 72.5,
        "nitrogen__pct_medium": 21.0,
        "nitrogen__pct_high": 6.5,
        "phosphorus__nutrient_index": 1.48,
        "phosphorus__pct_low": 60.0,
        "phosphorus__pct_medium": 32.0,
        "phosphorus__pct_high": 8.0,
        "potassium__nutrient_index": 2.52,
        "potassium__pct_low": 10.0,
        "potassium__pct_medium": 28.0,
        "potassium__pct_high": 62.0,
        "soil_ph__nutrient_index": 2.11,
        "soil_ph__pct_low": 5.0,
        "soil_ph__pct_medium": 79.0,
        "soil_ph__pct_high": 16.0,
        "organic_carbon__nutrient_index": 1.75,
        "organic_carbon__pct_low": 35.0,
        "organic_carbon__pct_medium": 55.0,
        "organic_carbon__pct_high": 10.0,
        "electrical_conductivity__nutrient_index": 1.05,
        "nitrogen__total_samples": 4200,
    }


def predict_fertilizer(
    input_data: Union[dict[str, Any], list[dict[str, Any]], pd.DataFrame]
) -> Union[dict[str, Any], list[dict[str, Any]], pd.DataFrame]:
    """Convenience top-level prediction function."""
    predictor = FertilizerPredictor()
    return predictor.predict(input_data)


if __name__ == "__main__":
    print("\n==========================================================")
    print("AgriAdapt AI: Fertilizer Recommendation Model Prediction")
    print("==========================================================")

    predictor = FertilizerPredictor()
    example = get_example_input()

    print("\n[Input Soil & Crop Profile]:")
    print(f"  Crop:       {example['crop']} ({example['crop_season']} season)")
    print(f"  Location:   {example['state_name']}")
    print(f"  Soil N Index:   {example['nitrogen__nutrient_index']} (Low fertility)")
    print(f"  Soil P Index:   {example['phosphorus__nutrient_index']} (Low-Medium fertility)")
    print(f"  Soil K Index:   {example['potassium__nutrient_index']} (High fertility)")
    print(f"  Soil pH Index:  {example['soil_ph__nutrient_index']} (Neutral)")

    prediction = predictor.predict(example)
    print("\n[Predicted Fertilizer Requirements]:")
    recs = prediction["recommendations"]
    for nut_key, data in recs.items():
        print(f"  * {nut_key.upper()} ({data['chemical_form']}): {data['value']} {data['unit']}")

    print("\n[Approximate Commercial Fertilizer Dosages]:")
    comm = prediction["fertilizer_commercial_equivalent_approx"]
    print(f"  * Urea (46% N): {comm['urea_46_pct_n_kg_ha']} kg/ha")
    print(f"  * DAP (46% P2O5): {comm['dap_46_pct_p2o5_kg_ha']} kg/ha")
    print(f"  * MOP (60% K2O):  {comm['mop_60_pct_k2o_kg_ha']} kg/ha")

    print(f"\n[Note/Disclaimer]: {prediction['disclaimer']}")
    print("==========================================================\n")
