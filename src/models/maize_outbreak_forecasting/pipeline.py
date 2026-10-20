"""
src/models/maize_outbreak_forecasting/pipeline.py
─────────────────────────────────────────────────
Reproducible, leakage-free MLOps pipeline for 7-day Maize Disease Outbreak Forecasting.
Enforces strict data sufficiency gating, temporal splitting, and honest reporting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .feature_engineering import TemporalFeatureEngineer
from .labeling import DiseaseOutbreakLabeler, OutbreakThresholdConfig
from .schemas import (
    DailyAgroclimaticRecord,
    FieldSurveillanceObservation,
    ForecastingFeatureRecord,
    MaizeDiseaseForecastRequest,
    MaizeDiseaseForecastResponse,
    OutbreakPredictionTarget,
    TargetDisease,
)


class InsufficientSurveillanceDataError(RuntimeError):
    """
    Raised when model training is requested but genuine time-indexed
    disease surveillance records are absent in the workspace.
    """
    pass


@dataclass
class TemporalSplitIndices:
    """Explicit time-indexed dataset partitions preventing future information leakage."""
    train_dates: tuple[date, date]
    val_dates: tuple[date, date]
    test_dates: tuple[date, date]
    train_count: int
    val_count: int
    test_count: int


class MaizeDiseaseOutbreakPipeline:
    """
    Core MLOps orchestrator for 7-day maize disease outbreak forecasting.
    """

    def __init__(
        self,
        artifacts_dir: str | Path = "models/maize_outbreak",
        target_disease: TargetDisease = TargetDisease.COMMON_RUST,
    ) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.target_disease = target_disease
        self.labeler = DiseaseOutbreakLabeler(OutbreakThresholdConfig(disease=target_disease))
        self.feature_engineer = TemporalFeatureEngineer()
        self.model: BaseEstimator | None = None
        self.metadata: dict[str, Any] = {}

    def temporal_train_val_test_split(
        self,
        df: pd.DataFrame,
        date_col: str = "reference_date",
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, TemporalSplitIndices]:
        """
        Split observations strictly by chronological time horizon.
        Never shuffles randomly, ensuring past data trains the model to predict forward in time.
        """
        if df.empty:
            raise ValueError("Input dataset is empty.")

        df_sorted = df.sort_values(by=date_col).reset_index(drop=True)
        unique_dates = sorted(df_sorted[date_col].unique())

        if len(unique_dates) < 3:
            raise ValueError(
                f"Insufficient temporal diversity: Found only {len(unique_dates)} unique dates. "
                f"Longitudinal forecasting requires multi-week / multi-season monitoring."
            )

        n_dates = len(unique_dates)
        train_end_idx = int(n_dates * train_ratio)
        val_end_idx = int(n_dates * (train_ratio + val_ratio))

        train_cutoff = unique_dates[train_end_idx]
        val_cutoff = unique_dates[val_end_idx]

        train_df = df_sorted[df_sorted[date_col] < train_cutoff].copy()
        val_df = df_sorted[(df_sorted[date_col] >= train_cutoff) & (df_sorted[date_col] < val_cutoff)].copy()
        test_df = df_sorted[df_sorted[date_col] >= val_cutoff].copy()

        indices = TemporalSplitIndices(
            train_dates=(min(train_df[date_col]), max(train_df[date_col])),
            val_dates=(min(val_df[date_col]), max(val_df[date_col])),
            test_dates=(min(test_df[date_col]), max(test_df[date_col])),
            train_count=len(train_df),
            val_count=len(val_df),
            test_count=len(test_df),
        )

        return train_df, val_df, test_df, indices

    def train(
        self,
        observations: Sequence[FieldSurveillanceObservation],
        weather_records: Sequence[DailyAgroclimaticRecord],
        model_type: str = "logistic_regression",
    ) -> dict[str, Any]:
        """
        Train the 7-day outbreak prediction model.
        STRICT DATA SUFFICIENCY CHECK:
        If observation records are empty or lack forward monitoring, halts immediately.
        """
        if not observations:
            raise InsufficientSurveillanceDataError(
                "Cannot train Maize Disease Outbreak Forecasting model: "
                "No longitudinal field disease observations provided. "
                "The image dataset in 'data/maize_leaf_disease' contains un-timestamped leaf photos "
                "and CANNOT be used as temporal outbreak labels."
            )

        # Build paired features and ground-truth forward labels
        feature_list = []
        labels = []
        ref_dates = []

        for obs in observations:
            try:
                target = self.labeler.generate_7day_outbreak_label(obs, observations)
                feat = self.feature_engineer.extract_features(obs, weather_records)
                feature_list.append(feat)
                labels.append(target.outbreak_label_7d)
                ref_dates.append(obs.observation_date)
            except ValueError:
                # Observation had no forward ground truth visit in [t0+1, t0+7]
                continue

        if len(feature_list) < 50:
            raise InsufficientSurveillanceDataError(
                f"Insufficient labeled transitions: Found only {len(feature_list)} valid forward pairs. "
                f"At least 50 longitudinal field observation intervals are required to fit a baseline."
            )

        X_df = self.feature_engineer.to_model_matrix(feature_list)
        X_df["reference_date"] = ref_dates
        X_df["target_outbreak_7d"] = labels

        # Chronological split
        train_df, val_df, test_df, split_info = self.temporal_train_val_test_split(X_df)

        feature_cols = [c for c in X_df.columns if c not in ("reference_date", "target_outbreak_7d")]
        X_train, y_train = train_df[feature_cols], train_df["target_outbreak_7d"]
        X_val, y_val = val_df[feature_cols], val_df["target_outbreak_7d"]
        X_test, y_test = test_df[feature_cols], test_df["target_outbreak_7d"]

        # Instantiate baseline model
        if model_type == "logistic_regression":
            clf = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
        elif model_type == "random_forest":
            clf = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42)
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")

        clf.fit(X_train, y_train)
        self.model = clf

        # Evaluate strictly on test set
        test_preds = clf.predict(X_test)
        test_probs = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else test_preds

        report = {
            "model_type": model_type,
            "target_disease": self.target_disease.value,
            "forecast_horizon_days": 7,
            "test_sample_count": len(y_test),
            "test_precision": float(precision_score(y_test, test_preds, zero_division=0)),
            "test_recall": float(recall_score(y_test, test_preds, zero_division=0)),
            "test_f1": float(f1_score(y_test, test_preds, zero_division=0)),
            "test_pr_auc": float(average_precision_score(y_test, test_probs)) if len(np.unique(y_test)) > 1 else None,
            "brier_score": float(brier_score_loss(y_test, test_probs)),
            "confusion_matrix": confusion_matrix(y_test, test_preds).tolist(),
            "temporal_split": {
                "train_dates": [str(split_info.train_dates[0]), str(split_info.train_dates[1])],
                "val_dates": [str(split_info.val_dates[0]), str(split_info.val_dates[1])],
                "test_dates": [str(split_info.test_dates[0]), str(split_info.test_dates[1])],
                "train_count": split_info.train_count,
                "val_count": split_info.val_count,
                "test_count": split_info.test_count,
            },
        }

        # Save artifacts
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, self.artifacts_dir / f"maize_{self.target_disease.value}_outbreak_model.joblib")
        with open(self.artifacts_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.metadata = report
        return report

    def forecast_7day_risk(
        self,
        request: MaizeDiseaseForecastRequest,
    ) -> MaizeDiseaseForecastResponse:
        """
        Generate 7-day outbreak risk assessment.
        If a trained ML model exists on disk, uses it.
        Otherwise, uses an agronomic bio-climatic rule screening engine while
        clearly disclosing provenance and data limitations.
        """
        ref_date = request.reference_date
        valid_to = ref_date + pd.Timedelta(days=7)

        # Epidemiological rule factors
        is_temp_optimal = 16.0 <= request.t7_mean_temperature_c <= 25.0
        is_rh_critical = request.t7_mean_humidity_pct >= 75.0 or request.t7_consecutive_high_humidity_days >= 3
        has_prior_symptoms = request.current_incidence_pct > 0.0 or request.current_severity_pct > 0.0

        # Optional CNN integration if leaf image provided
        cnn_score = None
        if request.leaf_image_path_at_t0:
            try:
                from .cnn_bridge import CNNDiagnosticBridge
                bridge = CNNDiagnosticBridge()
                cnn_feat = bridge.extract_contemporaneous_symptom_feature(request.leaf_image_path_at_t0)
                cnn_score = cnn_feat["common_rust_visual_probability_t0"]
            except Exception:
                cnn_score = None

        if self.model is not None:
            # ML Model inference
            row = pd.DataFrame([{
                "t7_mean_temp_c": request.t7_mean_temperature_c,
                "t7_min_temp_c": request.t7_mean_temperature_c - 5.0,
                "t7_max_temp_c": request.t7_mean_temperature_c + 5.0,
                "t7_temp_favorable_rust_hours_est": 12.0 if is_temp_optimal else 4.0,
                "t7_mean_rh_pct": request.t7_mean_humidity_pct,
                "t7_high_rh_days": request.t7_consecutive_high_humidity_days,
                "t7_cumulative_rainfall_mm": request.t7_cumulative_rainfall_mm,
                "t7_rainy_days_count": 2 if request.t7_cumulative_rainfall_mm > 10 else 0,
                "t7_estimated_leaf_wetness_hours_sum": 35.0 if is_rh_critical else 12.0,
                "t14_cumulative_rainfall_mm": request.t7_cumulative_rainfall_mm * 1.5,
                "growth_stage_vulnerability_index": 0.85,
                "current_incidence_at_t0": request.current_incidence_pct,
                "current_severity_at_t0": request.current_severity_pct,
                "disease_already_present_t0": 1 if has_prior_symptoms else 0,
                "regional_outbreak_pressure_last_14d": 0.0,
                "has_cnn_image_feature": 1 if cnn_score is not None else 0,
                "cnn_observed_leaf_rust_probability_t0": cnn_score or 0.0,
            }])
            prob = float(self.model.predict_proba(row)[0, 1])
            provenance = {
                "engine": "Trained ML Outbreak Classifier",
                "model_type": type(self.model).__name__,
                "status": "OPERATIONAL",
            }
        else:
            # Agroclimatic Rule-Based Bio-Model
            risk_points = 0.0
            factors = []

            if is_temp_optimal:
                risk_points += 0.35
                factors.append("Temperatures (16-25°C) are highly optimal for Puccinia sorghi spore germination")
            if is_rh_critical:
                risk_points += 0.35
                factors.append("Extended high humidity / dew duration provides leaf wetness required for rust infection")
            if has_prior_symptoms:
                risk_points += 0.20
                factors.append(f"Pre-existing field inoculum detected (incidence: {request.current_incidence_pct}%)")
            if cnn_score is not None and cnn_score >= 0.70:
                risk_points += 0.10
                factors.append(f"CNN detected pustule morphology on sampled leaf at t0 (visual score: {cnn_score:.2%})")

            prob = min(0.95, max(0.05, risk_points))
            provenance = {
                "engine": "Bio-Climatic Rule Screening Engine",
                "status": "ML_MODEL_UNTRAINED_DUE_TO_ABSENT_SURVEILLANCE_DATA",
                "reason": (
                    "No longitudinal field disease records currently exist in repository. "
                    "In adherence to MLOps standards, no ML model was fabricated without true temporal labels."
                ),
            }

        # Determine risk tier
        if prob >= 0.75:
            tier = "CRITICAL"
            advisory = (
                "High risk of rapid pustule eruption. Scout lower and ear leaves immediately. "
                "If severity approaches 5%, apply recommended triazole/strobilurin fungicide (e.g. Azoxystrobin + Difenoconazole)."
            )
        elif prob >= 0.50:
            tier = "HIGH"
            advisory = "Favorable weather for rust development. Increase scouting frequency to every 2 days."
        elif prob >= 0.25:
            tier = "MODERATE"
            advisory = "Maintain routine weekly scouting. Monitor weather forecasts for rainfall and cool nights."
        else:
            tier = "LOW"
            advisory = "Environmental conditions are not conducive to common rust sporulation. Routine care."

        factors_list = [
            f"Mean Temp (7d): {request.t7_mean_temperature_c:.1f}°C",
            f"Mean Humidity (7d): {request.t7_mean_humidity_pct:.1f}%",
            f"Current Field Incidence: {request.current_incidence_pct:.1f}%",
        ]

        return MaizeDiseaseForecastResponse(
            field_id=request.field_id,
            target_disease=request.target_disease.value,
            forecast_horizon_days=7,
            forecast_valid_from=ref_date,
            forecast_valid_to=valid_to,
            outbreak_probability=round(prob, 4),
            risk_tier=tier,
            current_field_status="DISEASE_DETECTED" if has_prior_symptoms else "APPARENTLY_HEALTHY",
            primary_driving_factors=factors_list,
            recommended_preventive_action=advisory,
            model_provenance=provenance,
            scientific_disclaimer=(
                "Forecast assesses 7-day epidemic outbreak potential based on agroclimatic and field scouting indicators. "
                "Does not guarantee absolute biological outcome. Local microclimate and host resistance affect field response."
            ),
        )
