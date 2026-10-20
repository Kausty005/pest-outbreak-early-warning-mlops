"""
tests/test_maize_outbreak_forecasting.py
────────────────────────────────────────
Unit and integration tests for the 7-day maize disease outbreak forecasting module.
Verifies data sufficiency gating, temporal label logic, feature causality, and CNN bridging.
"""

from __future__ import annotations

from datetime import date, timedelta
import pytest
import pandas as pd

from src.models.maize_outbreak_forecasting import (
    DailyAgroclimaticRecord,
    DiseaseOutbreakLabeler,
    DiseaseOccurrenceStatus,
    FieldSurveillanceObservation,
    InsufficientSurveillanceDataError,
    MaizeDiseaseForecastRequest,
    MaizeDiseaseOutbreakPipeline,
    MaizeGrowthStage,
    TargetDisease,
    TemporalFeatureEngineer,
    audit_project_data_sufficiency,
    CNNDiagnosticBridge,
)


def test_data_sufficiency_audit_detects_missing_longitudinal_records():
    """Verify that the auditor accurately flags the lack of longitudinal scouting and weather records."""
    audit = audit_project_data_sufficiency()
    assert audit.can_train_forecasting_model is False
    assert "MODEL TRAINING HALTED" in audit.decision_reason
    assert audit.historical_disease_surveillance_available is False
    assert audit.weather_sensor_data_available is False

    # Verify that existing datasets were audited
    dataset_paths = [d.path for d in audit.datasets_audited]
    assert any("Crop_recommendation.csv" in p for p in dataset_paths)
    assert any("maize_leaf_disease" in p for p in dataset_paths)


def test_outbreak_labeler_distinguishes_status_at_t0():
    """Verify correct categorization of disease presence on date t0."""
    labeler = DiseaseOutbreakLabeler()

    obs_clean = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 1), growth_stage=MaizeGrowthStage.MID_WHORL_V5_V8,
        incidence_pct=0.0, severity_pct=0.0,
    )
    assert labeler.determine_status_at_t0(obs_clean) == DiseaseOccurrenceStatus.ABSENT

    obs_trace = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 8), growth_stage=MaizeGrowthStage.MID_WHORL_V5_V8,
        incidence_pct=1.0, severity_pct=0.2,
    )
    assert labeler.determine_status_at_t0(obs_trace) == DiseaseOccurrenceStatus.DETECTED_TRACE

    obs_outbreak = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 15), growth_stage=MaizeGrowthStage.SILKING_R1,
        incidence_pct=40.0, severity_pct=8.5,
    )
    assert labeler.determine_status_at_t0(obs_outbreak) == DiseaseOccurrenceStatus.ACTIVE_OUTBREAK


def test_outbreak_labeler_7day_forward_transition():
    """Verify 7-day forward labeling: transition to >= 5% severity generates label = 1."""
    labeler = DiseaseOutbreakLabeler()

    t0_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 10), growth_stage=MaizeGrowthStage.LATE_WHORL_V9_VT,
        incidence_pct=3.0, severity_pct=0.8,
    )

    t_plus_5_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 15), growth_stage=MaizeGrowthStage.SILKING_R1,
        incidence_pct=35.0, severity_pct=6.5,  # Crossed 5% economic threshold
    )

    target = labeler.generate_7day_outbreak_label(t0_obs, [t0_obs, t_plus_5_obs])
    assert target.outbreak_label_7d == 1
    assert "economic injury threshold" in target.outbreak_reason.lower()


def test_outbreak_labeler_chronic_infection_not_counted_as_new_outbreak():
    """Verify that a field ALREADY in active outbreak at t0 is not labeled as a new outbreak."""
    labeler = DiseaseOutbreakLabeler()

    t0_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 10), growth_stage=MaizeGrowthStage.SILKING_R1,
        incidence_pct=50.0, severity_pct=10.0,  # Already outbreak at t0
    )

    t_plus_5_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 15), growth_stage=MaizeGrowthStage.SILKING_R1,
        incidence_pct=55.0, severity_pct=11.0,
    )

    target = labeler.generate_7day_outbreak_label(t0_obs, [t0_obs, t_plus_5_obs])
    # Prevents trivial self-correlation: field was already an active outbreak
    assert target.outbreak_label_7d == 0
    assert "already had an active outbreak at t0" in target.outbreak_reason


def test_outbreak_labeler_rejects_missing_forward_observations():
    """Verify that attempting to create a forward label with no future scouting raises ValueError."""
    labeler = DiseaseOutbreakLabeler()
    t0_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=date(2026, 7, 10), growth_stage=MaizeGrowthStage.MID_WHORL_V5_V8,
        incidence_pct=0.0, severity_pct=0.0,
    )

    with pytest.raises(ValueError, match="No future scouting visits exist"):
        labeler.generate_7day_outbreak_label(t0_obs, [t0_obs])


def test_temporal_feature_engineer_causality():
    """Verify feature extractor strictly relies on weather records prior to or on t0."""
    fe = TemporalFeatureEngineer()
    t0 = date(2026, 7, 10)

    t0_obs = FieldSurveillanceObservation(
        field_id="F1", latitude=15.0, longitude=75.0, state="KA", district="Dharwad",
        observation_date=t0, growth_stage=MaizeGrowthStage.SILKING_R1,
        incidence_pct=1.5, severity_pct=0.4,
    )

    # 10 days of past weather
    weather = []
    for d in range(14):
        w_date = t0 - timedelta(days=d)
        weather.append(DailyAgroclimaticRecord(
            field_id="F1", date=w_date,
            temp_max_c=26.0, temp_min_c=18.0, temp_mean_c=22.0,
            rh_morning_pct=88.0, rh_evening_pct=65.0, rh_mean_pct=76.0,
            rainfall_mm=5.0,
        ))

    feat = fe.extract_features(t0_obs, weather)
    assert feat.t7_mean_temp_c == 22.0
    assert feat.current_incidence_at_t0 == 1.5
    assert feat.disease_already_present_t0 == 1

    # Matrix conversion
    df = fe.to_model_matrix([feat])
    assert len(df) == 1
    assert "growth_stage_vulnerability_index" in df.columns
    assert df["growth_stage_vulnerability_index"].iloc[0] == 1.0  # Silking is peak vulnerable (1.0)


def test_pipeline_halts_training_without_surveillance_data():
    """Verify that calling train() without longitudinal data raises InsufficientSurveillanceDataError."""
    pipeline = MaizeDiseaseOutbreakPipeline()
    with pytest.raises(InsufficientSurveillanceDataError, match="No longitudinal field disease observations provided"):
        pipeline.train(observations=[], weather_records=[])


def test_pipeline_forecast_screening_provides_disclaimer():
    """Verify that risk screening works and includes data limitation disclosure."""
    pipeline = MaizeDiseaseOutbreakPipeline()
    req = MaizeDiseaseForecastRequest(
        field_id="FIELD-TEST-001",
        district="Davanagere",
        state="Karnataka",
        reference_date=date(2026, 10, 20),
        growth_stage=MaizeGrowthStage.MID_WHORL_V5_V8,
        target_disease=TargetDisease.COMMON_RUST,
        current_incidence_pct=1.0,
        current_severity_pct=0.2,
        t7_mean_temperature_c=21.0,
        t7_mean_humidity_pct=82.0,
        t7_cumulative_rainfall_mm=25.0,
        t7_consecutive_high_humidity_days=3,
    )

    resp = pipeline.forecast_7day_risk(req)
    assert resp.target_disease == "common_rust"
    assert resp.forecast_horizon_days == 7
    assert 0.0 <= resp.outbreak_probability <= 1.0
    assert resp.risk_tier in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert "ML_MODEL_UNTRAINED" in resp.model_provenance["status"]
    assert "Does not guarantee absolute biological outcome" in resp.scientific_disclaimer


def test_cnn_bridge_features_and_disclaimer():
    """Verify that CNN bridge produces valid symptom covariate with mandatory warning."""
    bridge = CNNDiagnosticBridge()
    sample_img = "data/maize_leaf_disease/common_rust/Corn_Common_Rust (349).JPG"

    import os
    if os.path.exists(sample_img):
        feat = bridge.extract_contemporaneous_symptom_feature(sample_img)
        assert "common_rust_visual_probability_t0" in feat
        assert 0.0 <= feat["common_rust_visual_probability_t0"] <= 1.0
        assert "MUST NOT be interpreted as a 7-day future outbreak probability" in feat["scientific_disclaimer"]
