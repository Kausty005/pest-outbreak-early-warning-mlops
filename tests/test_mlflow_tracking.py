from __future__ import annotations

from pathlib import Path

from backend.ml.train import TrainingConfig, run_training


def test_training_without_mlflow(tmp_path):
    dataset_csv = "data/raw/Crop_recommendation.csv"
    artifacts_dir = tmp_path / "artifacts"
    meta = run_training(
        dataset_path=dataset_csv,
        artifacts_dir=artifacts_dir,
        config=TrainingConfig(quick=True, cv_folds=2, mlflow_enabled=False),
    )
    assert meta["model_version"] is not None
    assert "mlflow" not in meta or meta["mlflow"] is None


def test_training_with_local_mlflow_tracking(tmp_path):
    dataset_csv = "data/raw/Crop_recommendation.csv"
    artifacts_dir = tmp_path / "artifacts"
    mlruns_dir = tmp_path / "mlruns"
    meta = run_training(
        dataset_path=dataset_csv,
        artifacts_dir=artifacts_dir,
        config=TrainingConfig(
            quick=True,
            cv_folds=2,
            mlflow_enabled=True,
            mlflow_tracking_uri=str(mlruns_dir.resolve()),
            mlflow_experiment="test-crop-experiment",
        ),
    )
    assert meta["model_version"] is not None
    assert "mlflow" in meta
    assert meta["mlflow"]["status"] == "tracked"
    run_id = meta["mlflow"]["run_id"]
    assert run_id is not None
    assert mlruns_dir.exists()

    # Query MLflow directly to verify logged parameters, metrics, and artifacts
    import mlflow
    from mlflow.tracking import MlflowClient

    client = MlflowClient(tracking_uri=meta["mlflow"]["tracking_uri"])
    run = client.get_run(run_id)
    assert run.info.run_id == run_id
    assert "selected_model" in run.data.params
    assert "dataset_checksum" in run.data.params
    assert "test_accuracy" in run.data.metrics
    assert "test_macro_f1" in run.data.metrics

    artifacts = [a.path for a in client.list_artifacts(run_id)]
    assert "metadata.json" in artifacts
    assert "model" in artifacts


def test_training_with_unreachable_mlflow_server_reports_honest_failure(tmp_path):
    dataset_csv = "data/raw/Crop_recommendation.csv"
    artifacts_dir = tmp_path / "artifacts"
    # Invalid tracking server URI scheme that fails immediately
    unreachable_uri = "invalid-scheme://localhost/test"
    meta = run_training(
        dataset_path=dataset_csv,
        artifacts_dir=artifacts_dir,
        config=TrainingConfig(
            quick=True,
            cv_folds=2,
            mlflow_enabled=True,
            mlflow_tracking_uri=unreachable_uri,
            mlflow_experiment="test-failure-experiment",
        ),
    )
    # Training still succeeds and produces valid model
    assert meta["model_version"] is not None
    assert (artifacts_dir / "crop_model.joblib").exists() or (artifacts_dir / "candidates").exists()
    # MLflow status honestly records failure without crash
    assert "mlflow" in meta
    assert meta["mlflow"]["status"] == "failed"
    assert "error" in meta["mlflow"]

