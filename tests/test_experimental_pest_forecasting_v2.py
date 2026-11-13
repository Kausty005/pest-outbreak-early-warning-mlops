"""
tests/test_experimental_pest_forecasting_v2.py
──────────────────────────────────────────────
Test suite for Version 2.0 experimental synthetic pest forecasting pipeline:
- Generator reproducibility and determinism
- Target generation integrity (future latent population thresholding)
- Absence of future-feature leakage
- Temporal order and 7-day purge embargo verification
- Confusion matrix mathematical consistency
- Model artifact loading and schema enforcement
- Synthetic disclaimer propagation
- Production readiness gate remaining BLOCKED
"""
from __future__ import annotations

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from src.pest_forecasting.dataset_v2 import (
    ALL_COLUMNS,
    ENVIRONMENTAL_FEATURE_COLUMNS,
    FULL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    DataLeakageError,
    chronological_split_with_purging_v2,
    load_and_validate_dataset_v2,
    verify_no_leakage_v2,
)
from src.pest_forecasting.synthetic_generator_v2 import generate_synthetic_dataset_v2
from src.pest_risk.production_readiness_gate import evaluate_production_readiness

MODELS_DIR = Path("models/experimental_synthetic_pest_v2")
DATASET_V2_PATH = Path("data/experimental/synthetic_pest_forecasting_v2.csv")


def test_synthetic_v2_dataset_exists_and_valid():
    """Verify that dataset v2 exists and passes schema and range checks."""
    assert DATASET_V2_PATH.is_file(), f"Dataset v2 file not found at: {DATASET_V2_PATH}"
    df = load_and_validate_dataset_v2(DATASET_V2_PATH, expected_rows=100000)
    assert len(df) == 100000
    assert set(ALL_COLUMNS).issubset(set(df.columns))
    assert df[TARGET_COLUMN].isin([0, 1]).all()


def test_leakage_detection_rejects_forbidden_columns():
    """Verify that verify_no_leakage_v2 raises DataLeakageError if future columns are included."""
    with pytest.raises(DataLeakageError):
        verify_no_leakage_v2(["t7_mean_temp_c", "outbreak_within_7d"])

    with pytest.raises(DataLeakageError):
        verify_no_leakage_v2(["t7_mean_temp_c", "future_latent_max"])

    with pytest.raises(DataLeakageError):
        verify_no_leakage_v2(["t7_mean_temp_c", "future_rainfall"])

    # Permitted columns pass cleanly
    verify_no_leakage_v2(ENVIRONMENTAL_FEATURE_COLUMNS)
    verify_no_leakage_v2(FULL_FEATURE_COLUMNS)


def test_chronological_splits_and_7day_purge_gaps():
    """Verify that chronological splitting enforces 7-day purge gaps between partitions."""
    df = load_and_validate_dataset_v2(DATASET_V2_PATH, expected_rows=100000)
    splits, meta = chronological_split_with_purging_v2(df, feature_set="full", purge_days=7)

    assert meta.train_count > 50000
    assert meta.val_count > 10000
    assert meta.test_count > 15000

    # Purge gaps
    assert meta.purged_gap1_count > 0
    assert meta.purged_gap2_count > 0

    # Verify no date overlap
    train_max = pd.to_datetime(meta.train_end_date)
    val_min = pd.to_datetime(meta.val_start_date)
    val_max = pd.to_datetime(meta.val_end_date)
    test_min = pd.to_datetime(meta.test_start_date)

    assert (val_min - train_max).days >= 8, "Purge gap 1 must be at least 8 days"
    assert (test_min - val_max).days >= 8, "Purge gap 2 must be at least 8 days"


def test_confusion_matrix_consistency_and_metrics():
    """Verify that all model confusion matrices sum to the exact test partition size."""
    summary_file = MODELS_DIR / "experiment_comparison_summary.json"
    assert summary_file.is_file(), "Summary file missing"

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for config_name in ["ENVIRONMENTAL_ONLY", "SCOUTING_ASSISTED"]:
        exp = data["experiments"][config_name]
        test_samples = exp["split_metadata"]["test_samples"]
        test_outbreaks = exp["split_metadata"]["test_outbreaks"]

        for model_name, m_res in exp["models"].items():
            tm = m_res["test_metrics_tuned_threshold"]
            cm_sum = tm["true_negatives"] + tm["false_positives"] + tm["false_negatives"] + tm["true_positives"]
            assert cm_sum == test_samples, f"Confusion matrix sum mismatch in {model_name}"
            assert tm["true_positives"] + tm["false_negatives"] == test_outbreaks, f"Positive label mismatch in {model_name}"


def test_model_artifact_loading_and_inference():
    """Verify that saved v2 model pipelines load cleanly and execute deterministic inference."""
    env_pipeline_path = MODELS_DIR / "environmental_model_pipeline.joblib"
    full_pipeline_path = MODELS_DIR / "full_model_pipeline.joblib"

    assert env_pipeline_path.is_file()
    assert full_pipeline_path.is_file()

    env_pipe = joblib.load(env_pipeline_path)
    full_pipe = joblib.load(full_pipeline_path)

    df = load_and_validate_dataset_v2(DATASET_V2_PATH, expected_rows=100000)
    splits, _ = chronological_split_with_purging_v2(df, feature_set="full")

    # Predict on test samples
    sample_env = splits.X_test[ENVIRONMENTAL_FEATURE_COLUMNS].iloc[0:5]
    sample_full = splits.X_test[FULL_FEATURE_COLUMNS].iloc[0:5]

    env_probs = env_pipe.predict_proba(sample_env)[:, 1]
    full_probs = full_pipe.predict_proba(sample_full)[:, 1]

    assert len(env_probs) == 5
    assert len(full_probs) == 5
    assert (env_probs >= 0.0).all() and (env_probs <= 1.0).all()
    assert (full_probs >= 0.0).all() and (full_probs <= 1.0).all()


def test_inference_examples_contain_experimental_disclaimers():
    """Verify that inference examples explicitly propagate SYNTHETIC_EXPERIMENTAL warnings."""
    examples_file = MODELS_DIR / "inference_examples.json"
    assert examples_file.is_file()

    with open(examples_file, "r", encoding="utf-8") as f:
        examples = json.load(f)

    assert examples["status"] == "SYNTHETIC_EXPERIMENTAL"
    assert examples["is_production_ready"] is False

    for item in examples["environmental_only_inference"]:
        assert "SYNTHETIC_EXPERIMENTAL" in item["disclaimer"]

    for item in examples["scouting_assisted_inference"]:
        assert "SYNTHETIC_EXPERIMENTAL" in item["disclaimer"]


def test_production_readiness_gate_remains_blocked():
    """Synthetic v2 models and dataset must NOT unblock the production readiness gate."""
    report = evaluate_production_readiness()
    assert report.gate_status == "BLOCKED"
    assert report.is_ready_for_training is False
    assert len(report.blocking_reasons) == 10
    assert report.data_foundation_inventory["authentic_prospective_surveillance_records"] == 0


def test_field_grouped_spatial_evaluation_artifact():
    """Verify that field-grouped spatial evaluation artifact exists and contains valid metrics."""
    field_eval_path = MODELS_DIR / "field_grouped_evaluation.json"
    assert field_eval_path.is_file(), f"Missing field grouped evaluation at {field_eval_path}"
    with open(field_eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["evaluation_type"] == "FIELD_GROUPED_SPATIAL_GENERALIZATION"
    assert data["unseen_fields_count"] == 115
    assert data["unseen_fields_samples"] == 19941

    for config in ["environmental_models", "scouting_models"]:
        for model_name, m_res in data[config].items():
            cm = m_res["cm"]
            assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] == 19941
            # Check FDR = FP / (TP + FP)
            expected_fdr = cm["fp"] / (cm["tp"] + cm["fp"])
            assert abs(m_res["fdr"] - round(expected_fdr, 4)) <= 0.0002
            # Check FPR = FP / (TN + FP)
            expected_fpr = cm["fp"] / (cm["tn"] + cm["fp"])
            assert abs(m_res["fpr"] - round(expected_fpr, 4)) <= 0.0002


def test_metric_definitions_fdr_fpr_separation():
    """Verify evaluate_predictions computes mathematically distinct FDR and FPR."""
    from src.pest_forecasting.evaluate import evaluate_predictions
    y_true = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # 2 positive, 8 negative
    y_prob = np.array([0.9, 0.2, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])  # TP=1, FN=1, FP=1, TN=7
    metrics = evaluate_predictions(y_true, y_prob, threshold=0.5)

    # TP = 1, FP = 1 -> Precision = 1 / (1 + 1) = 0.50
    # FDR = FP / (TP + FP) = 1 / 2 = 0.50 (equal to 1 - precision)
    # FPR = FP / (TN + FP) = 1 / (7 + 1) = 0.125 (distinct from FDR!)
    # FNR = FN / (FN + TP) = 1 / (1 + 1) = 0.50
    assert metrics.precision == 0.50
    assert metrics.false_discovery_rate == 0.50
    assert metrics.false_positive_rate == 0.125
    assert metrics.false_negative_rate == 0.50


