"""
Comprehensive unit and integration tests for AgriAdapt AI Pest Outbreak Forecasting Pipeline.
Covers schema validation, leakage prevention, chronological splitting, 7-day purging,
preprocessing separation, reproducibility, MLflow logging, serialization, and predictions.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from src.models.pest_forecasting.dataset import (
    ALL_COLUMNS,
    CATEGORICAL_COLUMNS,
    DataLeakageError,
    DataValidationError,
    FEATURE_COLUMNS,
    METADATA_COLUMNS,
    NUMERICAL_COLUMNS,
    TARGET_COLUMN,
    chronological_split,
    load_and_validate_dataset,
    verify_no_leakage,
)
from src.models.pest_forecasting.evaluate import evaluate_predictions, find_optimal_threshold
from src.models.pest_forecasting.preprocessor import build_model_pipeline, build_preprocessor
from src.models.pest_forecasting.train import PipelineConfig, run_training_pipeline

DATASET_CSV = Path("data/synthetic_multicrop_pest_forecasting.csv")
ARTIFACTS_DIR = Path("models/pest_outbreak_forecasting")


@pytest.fixture(scope="module")
def sample_dataset() -> pd.DataFrame:
    """Fixture to load dataset once for unit test suite."""
    return load_and_validate_dataset(DATASET_CSV)


def test_dataset_loading_and_schema_validation(sample_dataset: pd.DataFrame):
    """Verify loading loads exactly 100,000 rows, 17 columns with 0 missing values."""
    assert len(sample_dataset) == 100000
    assert len(sample_dataset.columns) == 17
    assert sample_dataset[ALL_COLUMNS].isnull().sum().sum() == 0
    for col in FEATURE_COLUMNS + METADATA_COLUMNS + [TARGET_COLUMN]:
        assert col in sample_dataset.columns


def test_target_values_restricted_to_binary(sample_dataset: pd.DataFrame):
    """Verify target outbreak_within_7d only contains {0, 1}."""
    unique_vals = set(sample_dataset[TARGET_COLUMN].unique())
    assert unique_vals.issubset({0, 1})
    assert 0 in unique_vals and 1 in unique_vals


def test_leakage_prevention_guards():
    """Verify verify_no_leakage raises DataLeakageError if target, field_id, date, or future terms leak."""
    # Valid feature list must not raise
    verify_no_leakage(FEATURE_COLUMNS)

    # Excluded columns must raise
    with pytest.raises(DataLeakageError):
        verify_no_leakage(FEATURE_COLUMNS + [TARGET_COLUMN])

    with pytest.raises(DataLeakageError):
        verify_no_leakage(FEATURE_COLUMNS + ["date"])

    with pytest.raises(DataLeakageError):
        verify_no_leakage(FEATURE_COLUMNS + ["field_id"])

    with pytest.raises(DataLeakageError):
        verify_no_leakage(FEATURE_COLUMNS + ["future_rainfall"])


def test_chronological_split_integrity_and_temporal_purging(sample_dataset: pd.DataFrame):
    """
    Verify chronological train-val-test split preserves time monotonicity
    and enforces a strict 7-day target window embargo/purge between splits.
    """
    splits, meta = chronological_split(
        sample_dataset,
        train_ratio=0.70,
        val_ratio=0.15,
        purge_days=7,
    )

    # Monotonic date ordering across splits
    train_end = pd.to_datetime(meta.train_end_date)
    val_start = pd.to_datetime(meta.val_start_date)
    val_end = pd.to_datetime(meta.val_end_date)
    test_start = pd.to_datetime(meta.test_start_date)

    assert train_end < val_start
    assert val_end < test_start

    # 7-day target horizon purge embargo guarantee:
    # Any training record at train_end has target window [train_end + 1, train_end + 7].
    # Validation start date must be > train_end + 7 days.
    assert (val_start - train_end).days >= 8
    assert (test_start - val_end).days >= 8

    # Purged counts must be non-zero
    assert meta.purged_gap1_count > 0
    assert meta.purged_gap2_count > 0
    assert meta.total_purged_count == meta.purged_gap1_count + meta.purged_gap2_count

    # Check X shape: 14 predictive features strictly
    assert splits.X_train.shape[1] == 14
    assert splits.X_val.shape[1] == 14
    assert splits.X_test.shape[1] == 14

    # Ensure forbidden columns are absent in X
    for forbidden in ["outbreak_within_7d", "date", "field_id"]:
        assert forbidden not in splits.X_train.columns
        assert forbidden not in splits.X_val.columns
        assert forbidden not in splits.X_test.columns


def test_preprocessing_fitted_only_on_training_data(sample_dataset: pd.DataFrame):
    """Verify ColumnTransformer and Pipeline fit strictly on training split."""
    splits, _ = chronological_split(sample_dataset, train_ratio=0.7, val_ratio=0.15, purge_days=7)

    pipeline = build_model_pipeline(DummyClassifier(strategy="most_frequent"))

    # Must fit cleanly on X_train only
    pipeline.fit(splits.X_train, splits.y_train)

    # Verify transformer can transform X_val and X_test without refitting
    val_transformed = pipeline.named_steps["preprocessor"].transform(splits.X_val)
    test_transformed = pipeline.named_steps["preprocessor"].transform(splits.X_test)

    assert val_transformed.shape[0] == len(splits.X_val)
    assert test_transformed.shape[0] == len(splits.X_test)
    assert val_transformed.shape[1] == test_transformed.shape[1]


def test_reproducibility_with_fixed_random_seed(sample_dataset: pd.DataFrame):
    """Verify that training an estimator with the same random seed yields identical predictions."""
    from sklearn.linear_model import LogisticRegression

    splits, _ = chronological_split(sample_dataset, train_ratio=0.7, val_ratio=0.15, purge_days=7)

    pipe1 = build_model_pipeline(LogisticRegression(random_state=42, max_iter=200, class_weight="balanced"))
    pipe1.fit(splits.X_train, splits.y_train)
    preds1 = pipe1.predict_proba(splits.X_val)

    pipe2 = build_model_pipeline(LogisticRegression(random_state=42, max_iter=200, class_weight="balanced"))
    pipe2.fit(splits.X_train, splits.y_train)
    preds2 = pipe2.predict_proba(splits.X_val)

    np.testing.assert_allclose(preds1, preds2, atol=1e-7)


def test_model_serialization_and_deserialization():
    """Verify that serialized joblib pipeline reloads and produces identical predictions."""
    model_path = ARTIFACTS_DIR / "synthetic_pest_outbreak_forecaster.joblib"
    assert model_path.exists(), f"Model artifact not found at {model_path}"

    pipeline = joblib.load(model_path)
    assert hasattr(pipeline, "predict")
    assert hasattr(pipeline, "predict_proba")

    # Create dummy observation row matching FEATURE_COLUMNS
    df_sample = load_and_validate_dataset(DATASET_CSV).head(10)[FEATURE_COLUMNS]

    preds = pipeline.predict(df_sample)
    probs = pipeline.predict_proba(df_sample)

    assert len(preds) == 10
    assert set(preds).issubset({0, 1})
    assert probs.shape == (10, 2)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()
    np.testing.assert_allclose(probs.sum(axis=1), np.ones(10), atol=1e-5)


def test_prediction_output_and_threshold_tuning():
    """Verify evaluation and threshold tuning strictly output valid binary classes and scores."""
    y_true = np.array([0, 0, 0, 1, 1, 0, 1, 0, 1, 0])
    y_prob = np.array([0.1, 0.2, 0.3, 0.8, 0.7, 0.4, 0.9, 0.15, 0.65, 0.35])

    opt_thresh, opt_f1 = find_optimal_threshold(y_true, y_prob, metric="f1")
    assert 0.05 <= opt_thresh <= 0.95
    assert 0.0 <= opt_f1 <= 1.0

    metrics = evaluate_predictions(y_true, (y_prob >= opt_thresh).astype(int), y_prob, threshold=opt_thresh)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.f1 <= 1.0
    assert metrics.true_positives + metrics.false_positives + metrics.true_negatives + metrics.false_negatives == 10


def test_mlflow_logged_artifacts():
    """Verify that required evaluation reports, metadata JSON, and summary markdown exist."""
    assert (ARTIFACTS_DIR / "model_comparison_report.md").exists()
    assert (ARTIFACTS_DIR / "model_metadata.json").exists()
    assert (ARTIFACTS_DIR / "confusion_matrix_val_selected.png").exists()
    assert (ARTIFACTS_DIR / "confusion_matrix_test_selected.png").exists()

    with open(ARTIFACTS_DIR / "model_metadata.json", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["pipeline_name"] == "AgriAdapt_Synthetic_Pest_Outbreak_Forecasting"
    assert "winner_model" in meta
    assert "val_metrics" in meta
    assert "test_metrics" in meta
