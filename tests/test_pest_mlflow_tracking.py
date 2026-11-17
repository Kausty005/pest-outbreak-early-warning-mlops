"""
tests/test_pest_mlflow_tracking.py
──────────────────────────────────
Integration tests for MLflow tracking in the Version 2.0 pest forecasting pipeline:
- Tracking both environmental-only and scouting-assisted runs.
- Verifying separate logging of training, validation, and test metrics.
- Verifying logging of parameters, hyperparameters, and dataset checksum.
- Verifying logged model artifacts and configuration files.
- Verifying graceful error handling for unreachable tracking servers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

import pytest

from src.pest_forecasting.train_v2 import run_training_and_stress_pipeline_v2

DATASET_PATH = Path("data/experimental/synthetic_pest_forecasting_v2.csv")


def test_pest_training_without_mlflow(tmp_path: Path):
    """Verify that training completes cleanly when MLflow tracking is disabled."""
    models_dir = tmp_path / "models_no_mlflow"
    summary = run_training_and_stress_pipeline_v2(
        dataset_path=DATASET_PATH,
        models_dir=models_dir,
        quick=True,
        mlflow_enabled=False,
    )
    assert summary is not None
    assert "experiments" in summary
    assert "mlflow" not in summary
    assert (models_dir / "environmental_model_pipeline.joblib").exists()
    assert (models_dir / "full_model_pipeline.joblib").exists()


def test_pest_training_with_local_mlflow_tracking(tmp_path: Path):
    """
    Verify complete local MLflow tracking for both environmental-only
    and scouting-assisted experiments with separate metrics and artifacts.
    """
    import mlflow
    from mlflow.tracking import MlflowClient

    models_dir = tmp_path / "models_mlflow"
    mlruns_dir = tmp_path / "mlruns"
    exp_name = "test-pest-v2-tracking-suite"

    summary = run_training_and_stress_pipeline_v2(
        dataset_path=DATASET_PATH,
        models_dir=models_dir,
        quick=True,
        mlflow_enabled=True,
        mlflow_tracking_uri=str(mlruns_dir.resolve()),
        mlflow_experiment=exp_name,
    )

    assert "mlflow" in summary
    mlflow_data = summary["mlflow"]
    assert "ENVIRONMENTAL_ONLY" in mlflow_data
    assert "SCOUTING_ASSISTED" in mlflow_data

    client = MlflowClient(tracking_uri=mlflow_data["ENVIRONMENTAL_ONLY"]["tracking_uri"])

    # 1. Verify ENVIRONMENTAL_ONLY run
    env_info = mlflow_data["ENVIRONMENTAL_ONLY"]
    assert env_info["status"] == "tracked"
    env_run = client.get_run(env_info["run_id"])

    # Verify Tags
    assert env_run.data.tags["model_domain"] == "pest_forecasting"
    assert env_run.data.tags["feature_configuration"] == "ENVIRONMENTAL_ONLY"
    assert env_run.data.tags["dataset_classification"] == "SYNTHETIC_EXPERIMENTAL_V2"
    assert env_run.data.tags["is_production_ready"] == "false"

    # Verify Parameters
    assert "dataset_checksum_sha256" in env_run.data.params
    assert env_run.data.params["feature_configuration"] == "ENVIRONMENTAL_ONLY"
    assert "optimal_threshold" in env_run.data.params
    assert "train_samples" in env_run.data.params
    assert "val_samples" in env_run.data.params
    assert "test_samples" in env_run.data.params

    # Verify Separate Metrics: Training, Validation, Test
    metrics = env_run.data.metrics
    assert "train_pr_auc" in metrics, "Missing training PR-AUC metric"
    assert "train_f1" in metrics, "Missing training F1 metric"
    assert "val_pr_auc" in metrics, "Missing validation PR-AUC metric"
    assert "val_f1" in metrics, "Missing validation F1 metric"
    assert "test_pr_auc" in metrics, "Missing test PR-AUC metric"
    assert "test_f1" in metrics, "Missing test F1 metric"
    assert "test_false_positive_rate" in metrics
    assert "test_false_alarm_burden" in metrics

    # Verify Logged Artifacts
    artifacts = [a.path for a in client.list_artifacts(env_info["run_id"])]
    assert "model" in artifacts, "Missing logged sklearn model artifact"
    assert "feature_schemas.json" in artifacts
    assert "experiment_comparison_summary.json" in artifacts

    # 2. Verify SCOUTING_ASSISTED run
    scout_info = mlflow_data["SCOUTING_ASSISTED"]
    assert scout_info["status"] == "tracked"
    scout_run = client.get_run(scout_info["run_id"])
    assert scout_run.data.tags["feature_configuration"] == "SCOUTING_ASSISTED"
    assert "train_pr_auc" in scout_run.data.metrics
    assert "val_pr_auc" in scout_run.data.metrics
    assert "test_pr_auc" in scout_run.data.metrics


def test_pest_training_with_unreachable_mlflow_reports_honest_failure(tmp_path: Path):
    """
    Verify that an unreachable MLflow server reports honest failure in metadata
    without aborting the training and artifact generation pipeline.
    """
    models_dir = tmp_path / "models_unreachable"
    summary = run_training_and_stress_pipeline_v2(
        dataset_path=DATASET_PATH,
        models_dir=models_dir,
        quick=True,
        mlflow_enabled=True,
        mlflow_tracking_uri="invalid-scheme://localhost/test",
        mlflow_experiment="unreachable-exp",
    )

    assert "mlflow" in summary
    assert summary["mlflow"]["ENVIRONMENTAL_ONLY"]["status"] == "failed"
    assert "error" in summary["mlflow"]["ENVIRONMENTAL_ONLY"]
    # Model artifacts were still produced safely
    assert (models_dir / "environmental_model_pipeline.joblib").exists()
    assert (models_dir / "full_model_pipeline.joblib").exists()
