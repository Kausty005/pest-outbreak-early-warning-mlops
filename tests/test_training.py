from __future__ import annotations

import json

import joblib

from backend.ml.data_validation import audit_dataframe
from backend.ml.train import TrainingConfig, run_training, train_from_dataframe

from .conftest import synthetic_frame


def test_training_compares_baseline_and_engineered_without_leakage(tmp_path):
    frame = synthetic_frame(rows_per_class=10)
    winner, results, split = train_from_dataframe(
        frame,
        audit_dataframe(frame).to_dict(),
        TrainingConfig(cv_folds=2, model_names=("random_forest",), quick=True),
    )
    assert {result.configuration for result in results} == {"baseline", "engineered"}
    assert split["train_rows"] == 24
    assert split["test_rows"] == 6
    assert winner.cv_macro_f1_mean >= 0


def test_training_saves_serialized_model_and_metadata(tmp_path):
    dataset_path = tmp_path / "test.csv"
    synthetic_frame(rows_per_class=10).to_csv(dataset_path, index=False)
    artifact_dir = tmp_path / "artifacts"
    metadata = run_training(
        dataset_path, artifact_dir, TrainingConfig(cv_folds=2, model_names=("extra_trees",), quick=True)
    )
    assert (artifact_dir / "crop_model.joblib").exists()
    assert (artifact_dir / "evaluation_report.md").exists()
    loaded = joblib.load(artifact_dir / "crop_model.joblib")
    assert list(loaded.classes_) == metadata["class_labels"]
    saved = json.loads((artifact_dir / "metadata.json").read_text())
    assert saved["dataset"]["checksum_sha256"]
    assert saved["feature_schema"]["input_features"] == ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
