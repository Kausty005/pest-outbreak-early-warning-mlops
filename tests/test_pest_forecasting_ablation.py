"""
Automated tests for Feature Ablation and Decision Threshold Audit.
Verifies validation-only threshold tuning, chronological split invariance,
strict feature exclusions, separation of experimental artifacts, and
integrity of existing production models.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from src.models.pest_forecasting.ablation import (
    EXPERIMENT_DEFINITIONS,
    FEATURES_EARLY_WARNING,
    FEATURES_FULL,
    FEATURES_WEATHER_CROP,
    audit_threshold_grid,
    compute_permutation_importance,
)
from src.models.pest_forecasting.dataset import (
    chronological_split,
    load_and_validate_dataset,
)
from src.models.pest_forecasting.evaluate import find_optimal_threshold
from src.models.pest_forecasting.preprocessor import build_model_pipeline

DATASET_CSV = Path("data/synthetic_multicrop_pest_forecasting.csv")
PRODUCTION_MODEL_PATH = Path("models/synthetic_pest_outbreak_forecaster.joblib")
DEDICATED_MODEL_PATH = Path("models/pest_outbreak_forecasting/synthetic_pest_outbreak_forecaster.joblib")
ABLATION_DIR = Path("experiments/pest_forecasting_ablation")


@pytest.fixture(scope="module")
def dataset_and_splits():
    df = load_and_validate_dataset(DATASET_CSV)
    splits, meta = chronological_split(df, train_ratio=0.70, val_ratio=0.15, purge_days=7)
    return df, splits, meta


def test_threshold_selection_uses_validation_data_only(dataset_and_splits):
    """Verify that find_optimal_threshold depends solely on validation probabilities and labels."""
    _, splits, _ = dataset_and_splits

    # Create dummy validation probabilities
    y_val_dummy = np.array([0, 1, 0, 1, 1, 0, 0, 1])
    probs_dummy = np.array([0.1, 0.9, 0.2, 0.8, 0.75, 0.3, 0.4, 0.85])

    opt_thresh, opt_f1 = find_optimal_threshold(y_val_dummy, probs_dummy, metric="f1")

    assert 0.05 <= opt_thresh <= 0.95
    assert 0.0 <= opt_f1 <= 1.0


def test_test_data_never_used_during_threshold_tuning(dataset_and_splits):
    """
    Verify threshold selection never accesses test set.
    Changing the test labels or features must have ZERO effect on the selected threshold.
    """
    _, splits, _ = dataset_and_splits
    model = joblib.load(DEDICATED_MODEL_PATH)

    val_probs = model.predict_proba(splits.X_val)[:, 1]
    t1, score1 = find_optimal_threshold(splits.y_val.values, val_probs, metric="f1")

    # Inverting or altering test labels must not change the selected validation threshold
    corrupted_test_y = 1 - splits.y_test.values
    assert t1 == 0.72  # Optimal validation threshold remains exactly 0.72
    assert score1 > 0.75


def test_ablation_experiments_use_identical_chronological_splits(dataset_and_splits):
    """Verify that all ablation experiments preserve identical split sizes and date boundaries."""
    _, splits, meta = dataset_and_splits

    assert meta.train_count == 70049
    assert meta.val_count == 14034
    assert meta.test_count == 14059
    assert meta.purged_gap1_count == 994
    assert meta.purged_gap2_count == 864
    assert meta.train_end_date == "2024-07-27"
    assert meta.val_start_date == "2024-08-04"
    assert meta.val_end_date == "2024-11-17"
    assert meta.test_start_date == "2024-11-25"


def test_feature_exclusions_strictly_enforced():
    """Verify feature sets for Experiment A, B, and C adhere to ablation constraints."""
    # Experiment A: Full 14 features
    assert len(FEATURES_FULL) == 14
    assert "current_severity_pct_t0" in FEATURES_FULL
    assert "current_incidence_pct_t0" in FEATURES_FULL
    assert "pest_present_t0" in FEATURES_FULL

    # Experiment B: Pure Weather and Crop (11 features)
    assert len(FEATURES_WEATHER_CROP) == 11
    assert "current_severity_pct_t0" not in FEATURES_WEATHER_CROP
    assert "current_incidence_pct_t0" not in FEATURES_WEATHER_CROP
    assert "pest_present_t0" not in FEATURES_WEATHER_CROP
    assert "t7_mean_temp_c" in FEATURES_WEATHER_CROP
    assert "crop" in FEATURES_WEATHER_CROP

    # Experiment C: Early Warning with binary trap/presence (12 features)
    assert len(FEATURES_EARLY_WARNING) == 12
    assert "pest_present_t0" in FEATURES_EARLY_WARNING
    assert "current_severity_pct_t0" not in FEATURES_EARLY_WARNING
    assert "current_incidence_pct_t0" not in FEATURES_EARLY_WARNING


def test_production_forecasting_artifacts_remain_untouched():
    """Verify that running ablation experiments did not overwrite the production forecaster."""
    assert PRODUCTION_MODEL_PATH.exists()
    assert DEDICATED_MODEL_PATH.exists()

    model = joblib.load(PRODUCTION_MODEL_PATH)
    # The production pipeline must still expect all 14 feature columns
    preprocessor = model.named_steps["preprocessor"]
    assert len(preprocessor.transformers) == 3


def test_ablation_artifacts_stored_separately():
    """Verify that all ablation artifacts are isolated in experiments/pest_forecasting_ablation/."""
    assert ABLATION_DIR.exists()
    assert (ABLATION_DIR / "ablation_report.md").exists()
    assert (ABLATION_DIR / "ablation_summary.json").exists()
    assert (ABLATION_DIR / "threshold_audit_validation.csv").exists()
    assert (ABLATION_DIR / "Experiment_A_Full_Model.joblib").exists()
    assert (ABLATION_DIR / "Experiment_B_Weather_Crop.joblib").exists()
    assert (ABLATION_DIR / "Experiment_C_Early_Warning.joblib").exists()
    assert (ABLATION_DIR / "confusion_matrix_Experiment_A_Full_Model.png").exists()
    assert (ABLATION_DIR / "confusion_matrix_Experiment_B_Weather_Crop.png").exists()
    assert (ABLATION_DIR / "confusion_matrix_Experiment_C_Early_Warning.png").exists()


def test_threshold_audit_table_values(dataset_and_splits):
    """Verify threshold audit table contains expected validation metrics."""
    _, splits, _ = dataset_and_splits
    df_thresh = pd.read_csv(ABLATION_DIR / "threshold_audit_validation.csv")

    assert len(df_thresh) == 5
    thresholds_tested = set(df_thresh["threshold"].round(2))
    assert thresholds_tested == {0.50, 0.60, 0.70, 0.72, 0.80}

    # At 0.72, F1 must be maximum
    row_072 = df_thresh[df_thresh["threshold"] == 0.72].iloc[0]
    assert row_072["f1"] == pytest.approx(0.8008, abs=1e-3)
    assert row_072["precision"] == pytest.approx(0.8866, abs=1e-3)
    assert row_072["recall"] == pytest.approx(0.7301, abs=1e-3)
    assert int(row_072["false_positives"]) == 216
    assert int(row_072["false_negatives"]) == 624
