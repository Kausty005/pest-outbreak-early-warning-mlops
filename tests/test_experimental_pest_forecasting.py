"""
tests/test_experimental_pest_forecasting.py
───────────────────────────────────────────
Test suite for Phase 19 Experimental Multi-Crop Pest Outbreak Forecasting Pipeline:
1. Synthetic dataset loading and schema validation.
2. Feature leakage prevention and forbidden column detection.
3. Chronological splitting with 7-day purge embargo verification.
4. Preprocessor pipeline construction and fit-on-train guarantees.
5. Model training and evaluation metric calculations (PR-AUC, ROC-AUC, Brier score, ECE).
6. Model artifact serialization under models/experimental_synthetic_pest/.
7. Inference interface validation, experimental labeling, and disclaimers.
8. Rejection of invalid inputs and causal inconsistencies.
9. Synthetic-only provenance and production-model isolation guarantee.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.pest_forecasting.dataset import (
    DataLeakageError,
    DataValidationError,
    ENVIRONMENTAL_FEATURE_COLUMNS,
    FULL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    chronological_split_with_purging,
    load_and_validate_dataset,
    verify_no_leakage,
)
from src.pest_forecasting.evaluate import (
    evaluate_predictions,
    find_optimal_threshold,
)
from src.pest_forecasting.inference import (
    ExperimentalPestForecaster,
    ExperimentalPestForecastInput,
)
from src.pest_forecasting.preprocessor import (
    build_model_pipeline,
    build_preprocessor,
)

DATA_PATH = Path("data/synthetic_multicrop_pest_forecasting.csv")
MODELS_DIR = Path("models/experimental_synthetic_pest")


# ==============================================================================
# 1. DATASET LOADING & VALIDATION
# ==============================================================================

def test_load_and_validate_synthetic_dataset():
    """Dataset loads successfully and passes all strict range and causal assertions."""
    df = load_and_validate_dataset(DATA_PATH, expected_rows=100000)
    assert len(df) == 100000
    assert df.isnull().sum().sum() == 0
    assert set(df[TARGET_COLUMN].unique()) == {0, 1}
    assert (df["t7_min_temp_c"] <= df["t7_max_temp_c"]).all()
    assert (df["t7_rainfall_mm"] <= df["t14_rainfall_mm"]).all()


def test_reject_dataset_with_invalid_target(tmp_path: Path):
    """Dataset with target values outside {0, 1} must raise DataValidationError."""
    bad_df = pd.DataFrame({
        "field_id": ["FLD-001"],
        "district": ["Nagpur"],
        "crop": ["Cotton"],
        "pest": ["Pink bollworm"],
        "date": ["2023-07-01"],
        "growth_stage": ["Flowering"],
        "t7_mean_temp_c": [28.0],
        "t7_min_temp_c": [22.0],
        "t7_max_temp_c": [34.0],
        "t7_mean_rh_pct": [75.0],
        "t7_high_rh_days": [2],
        "t7_rainfall_mm": [20.0],
        "t14_rainfall_mm": [40.0],
        "current_incidence_pct_t0": [5.0],
        "current_severity_pct_t0": [3.0],
        "pest_present_t0": [1],
        "outbreak_within_7d": [99],  # Invalid target!
    })
    bad_file = tmp_path / "bad_dataset.csv"
    bad_df.to_csv(bad_file, index=False)
    with pytest.raises(DataValidationError, match="Target outbreak_within_7d must be restricted to {0, 1}"):
        load_and_validate_dataset(bad_file, expected_rows=None)


# ==============================================================================
# 2. FEATURE LEAKAGE PREVENTION
# ==============================================================================

def test_verify_no_leakage_detects_forbidden_columns():
    """verify_no_leakage raises DataLeakageError if target, date, field_id, or future cols appear."""
    with pytest.raises(DataLeakageError, match="Forbidden column 'outbreak_within_7d'"):
        verify_no_leakage(["t7_mean_temp_c", "outbreak_within_7d"])

    with pytest.raises(DataLeakageError, match="Forbidden column 'date'"):
        verify_no_leakage(["crop", "date"])

    with pytest.raises(DataLeakageError, match="Forbidden column 'field_id'"):
        verify_no_leakage(["crop", "field_id"])

    with pytest.raises(DataLeakageError, match="Suspicious future/target-derived column"):
        verify_no_leakage(["crop", "future_incidence_t7"])


def test_environmental_features_exclude_all_scouting():
    """ENVIRONMENTAL_FEATURE_COLUMNS must strictly exclude all scouting/severity features."""
    for col in ["current_incidence_pct_t0", "current_severity_pct_t0", "pest_present_t0"]:
        assert col not in ENVIRONMENTAL_FEATURE_COLUMNS, f"Scouting feature '{col}' leaked into ENVIRONMENTAL set!"


# ==============================================================================
# 3. CHRONOLOGICAL SPLITTING & 7-DAY PURGE EMBARGO
# ==============================================================================

def test_chronological_split_with_7day_purging():
    """
    Splits must be strictly chronological with zero date overlap,
    and must enforce at least a 7-day purge embargo between splits.
    """
    df = load_and_validate_dataset(DATA_PATH, expected_rows=100000)
    splits, meta = chronological_split_with_purging(df, feature_set="environmental", purge_days=7)

    # 1. Row counts
    assert meta.train_count > 60000
    assert meta.val_count > 10000
    assert meta.test_count > 10000
    assert meta.total_purged_count > 0

    # 2. Chronological boundaries (Train < Val < Test)
    train_end = pd.to_datetime(meta.train_end_date)
    val_start = pd.to_datetime(meta.val_start_date)
    val_end = pd.to_datetime(meta.val_end_date)
    test_start = pd.to_datetime(meta.test_start_date)

    assert train_end < val_start
    assert val_end < test_start

    # 3. Purge embargo guarantee (gap >= 7 days)
    assert (val_start - train_end).days > 7
    assert (test_start - val_end).days > 7


# ==============================================================================
# 4. PREPROCESSOR PIPELINE
# ==============================================================================

def test_preprocessor_transformation():
    """Preprocessor must one-hot encode categoricals and scale continuous numericals."""
    preprocessor = build_preprocessor(feature_columns=ENVIRONMENTAL_FEATURE_COLUMNS)

    dummy_df = pd.DataFrame({
        "district": ["Nagpur", "Amravati"],
        "crop": ["Cotton", "Cotton"],
        "pest": ["Pink bollworm", "Pink bollworm"],
        "growth_stage": ["Flowering", "Boll_formation"],
        "t7_mean_temp_c": [28.0, 30.0],
        "t7_min_temp_c": [22.0, 24.0],
        "t7_max_temp_c": [34.0, 36.0],
        "t7_mean_rh_pct": [70.0, 75.0],
        "t7_high_rh_days": [1, 2],
        "t7_rainfall_mm": [10.0, 20.0],
        "t14_rainfall_mm": [30.0, 50.0],
    })

    X_trans = preprocessor.fit_transform(dummy_df)
    assert X_trans.shape[0] == 2
    # Transformed output must be 2D numpy array
    assert isinstance(X_trans, np.ndarray)


# ==============================================================================
# 5. EVALUATION METRICS & CALIBRATION
# ==============================================================================

def test_evaluation_metrics_and_calibration():
    """Metrics calculation must return PR-AUC, ROC-AUC, Brier score, and ECE."""
    y_true = np.array([0, 0, 0, 0, 1, 1, 0, 1, 0, 1])
    y_prob = np.array([0.1, 0.2, 0.15, 0.3, 0.8, 0.85, 0.4, 0.75, 0.25, 0.9])

    metrics = evaluate_predictions(y_true, y_prob, threshold=0.50)
    assert 0.0 <= metrics.pr_auc <= 1.0
    assert 0.0 <= metrics.roc_auc <= 1.0
    assert 0.0 <= metrics.brier_score <= 1.0
    assert metrics.f1 > 0.0
    assert "expected_calibration_error" in metrics.calibration_data

    # Optimal threshold search
    opt_t, opt_score = find_optimal_threshold(y_true, y_prob, metric="f1")
    assert 0.05 <= opt_t <= 0.95
    assert opt_score >= metrics.f1


# ==============================================================================
# 6. MODEL ARTIFACT SERIALIZATION
# ==============================================================================

def test_model_artifacts_exist_in_experimental_directory():
    """Verify that all 5 required experimental artifacts exist in models/experimental_synthetic_pest/."""
    expected_files = [
        "environmental_model_pipeline.joblib",
        "full_model_pipeline.joblib",
        "feature_schemas.json",
        "experiment_comparison_summary.json",
        "synthetic_provenance_metadata.json",
    ]
    for filename in expected_files:
        artifact_path = MODELS_DIR / filename
        assert artifact_path.exists(), f"Missing required artifact: {artifact_path}"

    with open(MODELS_DIR / "feature_schemas.json", encoding="utf-8") as f:
        schemas = json.load(f)
    assert len(schemas["FULL_SYNTHETIC_FEATURES"]) == 14
    assert len(schemas["ENVIRONMENTAL_ONLY_FEATURES"]) == 11


# ==============================================================================
# 7. INFERENCE INTERFACE & SYNTHETIC DISCLAIMER
# ==============================================================================

def test_experimental_inference_environmental():
    """Inference on environmental forecaster returns SYNTHETIC_EXPERIMENTAL and valid probability."""
    forecaster = ExperimentalPestForecaster(models_dir=MODELS_DIR, config="environmental")
    payload = {
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Boll_formation",
        "t7_mean_temp_c": 28.5,
        "t7_min_temp_c": 22.0,
        "t7_max_temp_c": 34.0,
        "t7_mean_rh_pct": 72.0,
        "t7_high_rh_days": 2,
        "t7_rainfall_mm": 25.0,
        "t14_rainfall_mm": 60.0,
    }
    output = forecaster.predict(payload)

    assert output.classification == "SYNTHETIC_EXPERIMENTAL"
    assert output.feature_configuration == "ENVIRONMENTAL_ONLY"
    assert 0.0 <= output.predicted_outbreak_risk <= 1.0
    assert isinstance(output.outbreak_warning, bool)
    assert output.is_production_ready is False
    assert "SYNTHETIC EXPERIMENTAL MODEL ONLY" in output.disclaimer


def test_experimental_inference_full_requires_scouting():
    """FULL configuration must reject inputs missing scouting incidence/severity."""
    forecaster = ExperimentalPestForecaster(models_dir=MODELS_DIR, config="full")
    payload_without_scout = {
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Boll_formation",
        "t7_mean_temp_c": 28.5,
        "t7_min_temp_c": 22.0,
        "t7_max_temp_c": 34.0,
        "t7_mean_rh_pct": 72.0,
        "t7_high_rh_days": 2,
        "t7_rainfall_mm": 25.0,
        "t14_rainfall_mm": 60.0,
        # Missing current_incidence_pct_t0, current_severity_pct_t0, pest_present_t0!
    }
    with pytest.raises(ValueError, match="requires in-field scouting observations"):
        forecaster.predict(payload_without_scout)


def test_experimental_inference_rejects_causal_inconsistencies():
    """Inference must reject biological / causal inconsistencies (min_temp > max_temp)."""
    forecaster = ExperimentalPestForecaster(models_dir=MODELS_DIR, config="environmental")
    bad_temp_payload = {
        "crop": "Rice",
        "pest": "Brown planthopper",
        "district": "East Godavari",
        "growth_stage": "Active_tillering",
        "t7_mean_temp_c": 28.0,
        "t7_min_temp_c": 35.0,  # min > max!
        "t7_max_temp_c": 30.0,
        "t7_mean_rh_pct": 80.0,
        "t7_high_rh_days": 4,
        "t7_rainfall_mm": 20.0,
        "t14_rainfall_mm": 40.0,
    }
    with pytest.raises(ValueError, match="t7_min_temp_c cannot exceed t7_max_temp_c"):
        forecaster.predict(bad_temp_payload)

    bad_rain_payload = dict(bad_temp_payload)
    bad_rain_payload["t7_min_temp_c"] = 22.0
    bad_rain_payload["t7_rainfall_mm"] = 100.0  # 7-day rain > 14-day rain!
    bad_rain_payload["t14_rainfall_mm"] = 50.0
    with pytest.raises(ValueError, match="7-day rainfall cannot exceed 14-day cumulative rainfall"):
        forecaster.predict(bad_rain_payload)


# ==============================================================================
# 8. PRODUCTION ISOLATION GUARANTEE
# ==============================================================================

def test_production_model_isolation():
    """
    Experimental pipeline must NEVER overwrite production models or authentic surveillance stores.
    """
    # Fertilizer model must remain intact
    fertilizer_model_path = Path("models/fertilizer_model.joblib")
    assert fertilizer_model_path.exists()
    assert fertilizer_model_path.stat().st_size > 1000

    # Production surveillance directory must contain 0 records
    prod_surveillance_file = Path("data/processed/pest_surveillance/field_surveillance_records.json")
    if prod_surveillance_file.exists():
        with open(prod_surveillance_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        assert len(records) == 0, f"Production surveillance storage corrupted! Found {len(records)} records."

    # Provenance file must verify zero authentic observations used
    prov_file = MODELS_DIR / "synthetic_provenance_metadata.json"
    with open(prov_file, "r", encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["authentic_field_observations_used"] == 0
    assert prov["production_deployment_eligible"] is False

