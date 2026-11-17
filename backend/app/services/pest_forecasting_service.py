"""
backend/app/services/pest_forecasting_service.py
────────────────────────────────────────────────
Production-isolated inference service for experimental Version 2.0
pest outbreak forecasting.
Integrates safe artifact loading, feature schema validation,
Prometheus telemetry, and strict synthetic experimental boundaries.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException, status

from backend.app.core.metrics import (
    pest_model_drift,
    pest_model_info,
    pest_prediction_errors_total,
    pest_prediction_latency_seconds,
    pest_prediction_requests_total,
)
from backend.app.schemas.pest_forecasting import (
    SCIENTIFIC_PEST_DISCLAIMER,
    PestForecastingRequest,
    PestForecastingResponse,
    PestModelInfoResponse,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_MODELS_DIR = Path("models/experimental_synthetic_pest_v2")


class PestForecastingService:
    """Thread-safe inference and model lifecycle service for experimental pest forecasting."""

    def __init__(self, models_dir: Path | str = DEFAULT_MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.environmental_pipeline: Any | None = None
        self.scouting_pipeline: Any | None = None
        self.feature_schemas: dict[str, list[str]] = {}
        self.model_config: dict[str, Any] = {}
        self.provenance_metadata: dict[str, Any] = {}
        self.decision_thresholds: dict[str, float] = {
            "environmental": 0.32,
            "scouting_assisted": 0.82,
        }
        self.model_version: str = "pest-v2.0.0-experimental-synthetic"
        self.environmental_model_type: str = "RandomForest"
        self.scouting_model_type: str = "LightGBM"
        self.loaded: bool = False

    def load(self) -> None:
        """Safely load trained pipeline artifacts, schemas, and calibration thresholds."""
        if not self.models_dir.exists():
            LOGGER.warning("Pest forecasting models directory does not exist: %s", self.models_dir)
            self.loaded = False
            return

        # 1. Feature Schemas
        schema_path = self.models_dir / "feature_schemas.json"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    self.feature_schemas = json.load(f)
            except Exception as exc:
                LOGGER.error("Failed to load feature schemas: %s", exc)

        # 2. Model Config & Decision Thresholds
        config_path = self.models_dir / "model_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.model_config = json.load(f)
                    thresholds = self.model_config.get("decision_thresholds", {})
                    if "environmental" in thresholds:
                        self.decision_thresholds["environmental"] = float(thresholds["environmental"])
                    if "scouting_assisted" in thresholds:
                        self.decision_thresholds["scouting_assisted"] = float(thresholds["scouting_assisted"])
                    self.environmental_model_type = self.model_config.get("environmental_best_model", "RandomForest")
                    self.scouting_model_type = self.model_config.get("scouting_best_model", "LightGBM")
            except Exception as exc:
                LOGGER.error("Failed to load model config: %s", exc)

        # 3. Provenance Metadata
        provenance_path = self.models_dir / "synthetic_provenance_metadata.json"
        if provenance_path.exists():
            try:
                with open(provenance_path, "r", encoding="utf-8") as f:
                    self.provenance_metadata = json.load(f)
                    self.model_version = self.provenance_metadata.get(
                        "pipeline_version", "pest-v2.0.0-experimental-synthetic"
                    )
            except Exception as exc:
                LOGGER.error("Failed to load provenance metadata: %s", exc)

        # 4. Pipelines
        env_file = self.models_dir / "environmental_model_pipeline.joblib"
        if env_file.exists():
            try:
                self.environmental_pipeline = joblib.load(env_file)
                LOGGER.info("Loaded environmental pest forecasting pipeline from %s", env_file)
            except Exception as exc:
                LOGGER.error("Failed to load environmental pipeline: %s", exc)
                self.environmental_pipeline = None

        full_file = self.models_dir / "full_model_pipeline.joblib"
        if full_file.exists():
            try:
                self.scouting_pipeline = joblib.load(full_file)
                LOGGER.info("Loaded scouting-assisted pest forecasting pipeline from %s", full_file)
            except Exception as exc:
                LOGGER.error("Failed to load scouting-assisted pipeline: %s", exc)
                self.scouting_pipeline = None

        self.loaded = self.environmental_pipeline is not None or self.scouting_pipeline is not None

        # 5. Register Prometheus Model Info
        if self.environmental_pipeline is not None:
            pest_model_info.labels(
                model_version=self.model_version,
                configuration="ENVIRONMENTAL_ONLY",
                framework="scikit-learn",
                is_synthetic="true",
                is_production_ready="false",
            ).set(1)

        if self.scouting_pipeline is not None:
            pest_model_info.labels(
                model_version=self.model_version,
                configuration="SCOUTING_ASSISTED",
                framework="scikit-learn",
                is_synthetic="true",
                is_production_ready="false",
            ).set(1)

    def get_model_info(self) -> PestModelInfoResponse:
        """Return metadata describing active experimental models and readiness gates."""
        return PestModelInfoResponse(
            service_status="ok" if self.loaded else "degraded",
            environmental_model_available=self.environmental_pipeline is not None,
            scouting_model_available=self.scouting_pipeline is not None,
            model_version=self.model_version,
            classification="SYNTHETIC_EXPERIMENTAL",
            is_production_ready=False,
            production_readiness_status="BLOCKED",
            environmental_model_type=self.environmental_model_type,
            scouting_model_type=self.scouting_model_type,
            decision_thresholds=self.decision_thresholds,
            feature_schemas=self.feature_schemas,
            disclaimer=SCIENTIFIC_PEST_DISCLAIMER,
        )

    def predict(self, request: PestForecastingRequest) -> PestForecastingResponse:
        """
        Execute experimental pest outbreak forecast inference.
        Tracks Prometheus metrics and applies decision thresholds.
        """
        cfg = request.configuration.strip().upper()
        norm_cfg_label = "ENVIRONMENTAL_ONLY" if cfg == "ENVIRONMENTAL_ONLY" else "SCOUTING_ASSISTED"
        start_time = time.perf_counter()

        # Check model availability
        pipeline = (
            self.environmental_pipeline
            if norm_cfg_label == "ENVIRONMENTAL_ONLY"
            else self.scouting_pipeline
        )

        if pipeline is None:
            pest_prediction_errors_total.labels(error_type="model_unavailable").inc()
            pest_prediction_requests_total.labels(configuration=norm_cfg_label.lower(), status="error").inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Pest forecasting pipeline for configuration '{norm_cfg_label}' is currently unavailable. "
                    f"Ensure model artifacts exist in {self.models_dir}."
                ),
            )

        try:
            # Build input DataFrame matching exact feature schema
            row_dict = request.model_dump()
            expected_cols = (
                self.feature_schemas.get("environmental_features")
                if norm_cfg_label == "ENVIRONMENTAL_ONLY"
                else self.feature_schemas.get("scouting_assisted_features")
            )

            if not expected_cols:
                # Fallback to standard column sets if schema file wasn't loaded
                expected_cols = [
                    "district", "crop", "pest", "growth_stage",
                    "t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c",
                    "t7_mean_rh_pct", "t7_rainfall_mm", "t14_rainfall_mm",
                    "t7_mean_soil_moisture", "t7_high_rh_days", "t7_consecutive_dry_days",
                ]
                if norm_cfg_label == "SCOUTING_ASSISTED":
                    expected_cols += [
                        "scout_incidence_pct", "scout_severity_pct",
                        "trap_catch_count", "days_since_scouting", "pest_present",
                    ]

            df_input = pd.DataFrame([{col: row_dict.get(col) for col in expected_cols}])

            # Execute pipeline prediction
            proba = float(pipeline.predict_proba(df_input)[0, 1])
            thresh_key = "environmental" if norm_cfg_label == "ENVIRONMENTAL_ONLY" else "scouting_assisted"
            thresh = float(self.decision_thresholds.get(thresh_key, 0.50))
            warning = bool(proba >= thresh)

            # Categorize risk level
            if proba >= thresh:
                risk_level = "HIGH"
            elif proba >= (thresh * 0.60):
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            # Record Prometheus metrics
            duration = time.perf_counter() - start_time
            pest_prediction_latency_seconds.labels(configuration=norm_cfg_label.lower()).observe(duration)
            pest_prediction_requests_total.labels(configuration=norm_cfg_label.lower(), status="success").inc()

            # Update feature drift monitoring indicator (simple normalized distance from typical bounds)
            # Reference baseline midpoints for key meteorological features
            pest_model_drift.labels(feature="temperature_anomaly", metric="abs_diff").set(
                abs(request.t7_mean_temp_c - 28.5)
            )
            pest_model_drift.labels(feature="humidity_anomaly", metric="abs_diff").set(
                abs(request.t7_mean_rh_pct - 70.0)
            )

            return PestForecastingResponse(
                classification="SYNTHETIC_EXPERIMENTAL",
                is_production_ready=False,
                feature_configuration=norm_cfg_label,
                outbreak_risk_probability=round(proba, 4),
                outbreak_warning=warning,
                decision_threshold=round(thresh, 3),
                risk_level=risk_level,
                model_version=self.model_version,
                model_family=self.environmental_model_type if norm_cfg_label == "ENVIRONMENTAL_ONLY" else self.scouting_model_type,
                prediction_horizon_days=7,
                disclaimer=SCIENTIFIC_PEST_DISCLAIMER,
                input_summary={
                    "crop": request.crop,
                    "pest": request.pest,
                    "district": request.district,
                    "growth_stage": request.growth_stage,
                    "t7_mean_temp_c": request.t7_mean_temp_c,
                    "t7_mean_rh_pct": request.t7_mean_rh_pct,
                    "t7_rainfall_mm": request.t7_rainfall_mm,
                    "t7_mean_soil_moisture": request.t7_mean_soil_moisture,
                    "configuration": norm_cfg_label,
                },
            )

        except HTTPException:
            raise
        except Exception as exc:
            LOGGER.exception("Error executing pest forecasting inference: %s", exc)
            pest_prediction_errors_total.labels(error_type="inference_error").inc()
            pest_prediction_requests_total.labels(configuration=norm_cfg_label.lower(), status="error").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference error during pest outbreak forecasting: {exc}",
            )

    def get_example(self, configuration: str = "ENVIRONMENTAL_ONLY") -> dict[str, Any]:
        """Return verified sample payloads for either configuration."""
        norm = configuration.strip().upper()
        base = {
            "configuration": norm,
            "crop": "Cotton",
            "pest": "Pink bollworm",
            "district": "Nagpur",
            "growth_stage": "Squaring",
            "t7_mean_temp_c": 31.5,
            "t7_min_temp_c": 26.2,
            "t7_max_temp_c": 36.8,
            "t7_mean_rh_pct": 78.4,
            "t7_rainfall_mm": 12.5,
            "t14_rainfall_mm": 45.0,
            "t7_mean_soil_moisture": 0.385,
            "t7_high_rh_days": 4,
            "t7_consecutive_dry_days": 2,
        }
        if norm == "SCOUTING_ASSISTED":
            base.update({
                "scout_incidence_pct": 14.5,
                "scout_severity_pct": 8.0,
                "trap_catch_count": 18.0,
                "days_since_scouting": 3.0,
                "pest_present": 1,
            })
        return base
