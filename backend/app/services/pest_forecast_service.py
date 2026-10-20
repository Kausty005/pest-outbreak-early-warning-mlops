"""
AgriAdapt AI — Pest Outbreak Forecasting Service.
Encapsulates model artifact loading, input validation, feature alignment,
inference execution, and threshold classification for 7-day outbreak forecasting.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ..schemas.pest_forecast import (
    PestForecastCatalogInfo,
    PestForecastRequest,
    PestForecastResponse,
    VALID_CROP_PEST_PAIRS,
)

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SYNTHETIC_DATA_DISCLAIMER = (
    "All training and evaluation results are based on entirely synthetic agricultural data. "
    "They demonstrate pipeline functionality and performance on simulated assumptions only. "
    "They do not establish real-world pest outbreak forecasting accuracy and must not be used "
    "for operational farm advisories."
)

GROWTH_STAGES_BY_CROP: dict[str, list[str]] = {
    "Maize": ["V1_V4_early_whorl", "V5_V8_mid_whorl", "V9_VT_late_whorl", "R1_silking", "R2_R4_grain_fill", "R5_R6_maturity"],
    "Rice": ["Seedling_transplanting", "Active_tillering", "Panicle_initiation", "Booting_heading", "Milky_dough", "Ripening_maturity"],
    "Cotton": ["Vegetative", "Squaring_bud", "Flowering", "Boll_formation", "Boll_maturation", "Bursting_picking"],
    "Wheat": ["Crown_root_initiation", "Tillering", "Jointing_stem_extension", "Booting_heading", "Milky_grain", "Dough_maturity"],
    "Tomato": ["Vegetative_branching", "Flowering", "Fruit_setting", "Fruit_development", "Harvest_ripening"],
    "Chickpea": ["Seedling", "Vegetative_branching", "Flowering", "Early_pod_formation", "Pod_filling", "Maturity_senescence"],
}

SAMPLE_DISTRICTS = [
    "Davanagere", "Belagavi", "Chhindwara", "Nagpur", "Amravati",
    "East Godavari", "Thanjavur", "Ludhiana", "Karnal", "Kolar",
    "Nashik", "Pune", "Kalaburagi", "Akola", "Vidisha", "Cuttack"
]


class ModelLoadError(RuntimeError):
    """Raised when a required forecasting model artifact cannot be found or loaded."""
    pass


class PestForecastService:
    """
    Independent service orchestrating 7-day pest outbreak predictions.
    Supports Full Model (Experiment A), Weather & Crop Model (Experiment B),
    and Early-Warning Model (Experiment C).
    """

    MODEL_CONFIGS = {
        "full": {
            "label": "Full-Feature Forecasting Model (Experiment A)",
            "description": "Uses full microclimatic weather, crop phenology, and in-field scouting infestation metrics.",
            "artifact_path": PROJECT_ROOT / "models" / "synthetic_pest_outbreak_forecaster.joblib",
            "fallback_artifact_path": PROJECT_ROOT / "experiments" / "pest_forecasting_ablation" / "Experiment_A_Full_Model.joblib",
            "threshold": 0.72,
            "required_features": [
                "district", "crop", "pest", "growth_stage",
                "t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c",
                "t7_mean_rh_pct", "t7_high_rh_days", "t7_rainfall_mm", "t14_rainfall_mm",
                "current_incidence_pct_t0", "current_severity_pct_t0", "pest_present_t0",
            ],
            "infestation_required": True,
            "binary_presence_required": True,
        },
        "weather_crop": {
            "label": "Weather & Crop Model (Experiment B)",
            "description": "Macro-level early warning using only weather and crop phenology. Requires zero field scouting.",
            "artifact_path": PROJECT_ROOT / "experiments" / "pest_forecasting_ablation" / "Experiment_B_Weather_Crop.joblib",
            "fallback_artifact_path": None,
            "threshold": 0.42,
            "required_features": [
                "district", "crop", "pest", "growth_stage",
                "t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c",
                "t7_mean_rh_pct", "t7_high_rh_days", "t7_rainfall_mm", "t14_rainfall_mm",
            ],
            "infestation_required": False,
            "binary_presence_required": False,
        },
        "early_warning": {
            "label": "Binary Early-Warning Model (Experiment C)",
            "description": "Intermediate warning model combining weather and binary pest trap detection, without quantitative foliar damage scoring.",
            "artifact_path": PROJECT_ROOT / "experiments" / "pest_forecasting_ablation" / "Experiment_C_Early_Warning.joblib",
            "fallback_artifact_path": None,
            "threshold": 0.56,
            "required_features": [
                "district", "crop", "pest", "growth_stage",
                "t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c",
                "t7_mean_rh_pct", "t7_high_rh_days", "t7_rainfall_mm", "t14_rainfall_mm",
                "pest_present_t0",
            ],
            "infestation_required": False,
            "binary_presence_required": True,
        },
    }

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self.load_models()

    def load_models(self) -> None:
        """Load trained forecasting artifacts into memory."""
        for model_key, cfg in self.MODEL_CONFIGS.items():
            primary_path = Path(cfg["artifact_path"])
            fallback_path = Path(cfg["fallback_artifact_path"]) if cfg.get("fallback_artifact_path") else None

            path_to_load = None
            if primary_path.exists():
                path_to_load = primary_path
            elif fallback_path and fallback_path.exists():
                path_to_load = fallback_path

            if path_to_load:
                try:
                    self._models[model_key] = joblib.load(path_to_load)
                    LOGGER.info("Loaded forecasting model '%s' from %s", model_key, path_to_load)
                except Exception as exc:
                    LOGGER.error("Failed to load model '%s' from %s: %s", model_key, path_to_load, exc)
            else:
                LOGGER.warning("Forecasting artifact for '%s' not found at %s", model_key, primary_path)

    def is_available(self, model_type: str = "full") -> bool:
        return model_type in self._models

    def get_catalog_info(self) -> PestForecastCatalogInfo:
        """Return discovery information for frontend form configuration."""
        items = []
        for key, cfg in self.MODEL_CONFIGS.items():
            items.append({
                "model_type": key,
                "label": cfg["label"],
                "description": cfg["description"],
                "required_features": cfg["required_features"],
                "decision_threshold": cfg["threshold"],
                "available": key in self._models,
            })

        return PestForecastCatalogInfo(
            available_models=items,
            crop_pest_pairs={k.capitalize(): v for k, v in VALID_CROP_PEST_PAIRS.items()},
            growth_stages_by_crop=GROWTH_STAGES_BY_CROP,
            sample_districts=SAMPLE_DISTRICTS,
            disclaimer=SYNTHETIC_DATA_DISCLAIMER,
        )

    def predict(self, req: PestForecastRequest) -> PestForecastResponse:
        """
        Execute 7-day pest outbreak prediction with strict validation.
        """
        model_type = req.model_type
        if model_type not in self.MODEL_CONFIGS:
            raise ValueError(f"Unknown model_type '{model_type}'. Choose from: 'full', 'weather_crop', 'early_warning'.")

        cfg = self.MODEL_CONFIGS[model_type]
        if model_type not in self._models:
            raise ModelLoadError(
                f"Forecasting model artifact for '{model_type}' is unavailable. "
                f"Expected location: {cfg['artifact_path']}"
            )

        model = self._models[model_type]

        # 1. Validate Crop & Pest matching
        crop_clean = req.crop.strip().lower()
        if crop_clean not in VALID_CROP_PEST_PAIRS:
            valid_crops = [c.capitalize() for c in VALID_CROP_PEST_PAIRS.keys()]
            raise ValueError(f"Crop '{req.crop}' is not supported for pest forecasting. Supported: {valid_crops}")

        expected_pest = VALID_CROP_PEST_PAIRS[crop_clean]
        if req.pest.strip().lower() != expected_pest.lower():
            raise ValueError(
                f"Target pest mismatch! For crop '{req.crop.capitalize()}', the supported pest is "
                f"'{expected_pest}', but received '{req.pest}'."
            )

        # 2. Validate feature completeness according to selected model
        if cfg["infestation_required"]:
            missing = []
            if req.current_incidence_pct_t0 is None:
                missing.append("current_incidence_pct_t0")
            if req.current_severity_pct_t0 is None:
                missing.append("current_severity_pct_t0")
            if req.pest_present_t0 is None:
                missing.append("pest_present_t0")
            if missing:
                raise ValueError(
                    f"Model '{model_type}' requires field scouting infestation features: {missing}. "
                    f"If scouting data is unavailable, select model_type='weather_crop' or 'early_warning'."
                )

        if cfg["binary_presence_required"] and req.pest_present_t0 is None:
            raise ValueError(
                f"Model '{model_type}' requires 'pest_present_t0' (0 or 1 binary trap/symptom indicator)."
            )

        # 3. Assemble feature row DataFrame strictly matching training columns
        features_needed = cfg["required_features"]
        row_dict: dict[str, Any] = {
            "district": req.district.strip(),
            "crop": crop_clean.capitalize(),
            "pest": expected_pest,
            "growth_stage": req.growth_stage.strip(),
            "t7_mean_temp_c": float(req.t7_mean_temp_c),
            "t7_min_temp_c": float(req.t7_min_temp_c),
            "t7_max_temp_c": float(req.t7_max_temp_c),
            "t7_mean_rh_pct": float(req.t7_mean_rh_pct),
            "t7_high_rh_days": int(req.t7_high_rh_days),
            "t7_rainfall_mm": float(req.t7_rainfall_mm),
            "t14_rainfall_mm": float(req.t14_rainfall_mm),
        }

        if "pest_present_t0" in features_needed:
            row_dict["pest_present_t0"] = int(req.pest_present_t0 or 0)
        if "current_incidence_pct_t0" in features_needed:
            row_dict["current_incidence_pct_t0"] = float(req.current_incidence_pct_t0 or 0.0)
        if "current_severity_pct_t0" in features_needed:
            row_dict["current_severity_pct_t0"] = float(req.current_severity_pct_t0 or 0.0)

        # CRITICAL LEAKAGE GUARD: Ensure forbidden columns are never passed
        for forbidden in ["field_id", "date", "outbreak_within_7d"]:
            row_dict.pop(forbidden, None)

        df_input = pd.DataFrame([row_dict])[features_needed]

        # 4. Generate prediction
        prob = float(model.predict_proba(df_input)[0, 1])
        prob = round(float(np.clip(prob, 0.0, 1.0)), 4)
        threshold = cfg["threshold"]
        outbreak_predicted = bool(prob >= threshold)
        risk_level = "HIGH OUTBREAK RISK" if outbreak_predicted else "LOW / NORMAL RISK"

        return PestForecastResponse(
            crop=crop_clean.capitalize(),
            target_pest=expected_pest,
            forecast_horizon="7 days",
            outbreak_probability=prob,
            outbreak_predicted=outbreak_predicted,
            risk_level=risk_level,
            decision_threshold=threshold,
            model_used=model_type,
            model_label=cfg["label"],
            features_used=features_needed,
            disclaimer=SYNTHETIC_DATA_DISCLAIMER,
            input_summary={
                "crop": crop_clean.capitalize(),
                "pest": expected_pest,
                "district": req.district,
                "growth_stage": req.growth_stage,
                "t7_mean_temp_c": req.t7_mean_temp_c,
                "t7_mean_rh_pct": req.t7_mean_rh_pct,
                "t7_rainfall_mm": req.t7_rainfall_mm,
                "model_type": model_type,
            },
        )
