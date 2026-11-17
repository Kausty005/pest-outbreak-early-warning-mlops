from __future__ import annotations

from pathlib import Path

import yaml

from backend.ml.fertilizer import verify_fertilizer_artifacts


def test_dvc_yaml_structure_and_dependencies():
    dvc_file = Path("dvc.yaml")
    assert dvc_file.exists()

    config = yaml.safe_load(dvc_file.read_text(encoding="utf-8"))
    assert "stages" in config
    stages = config["stages"]

    # Verify stage names
    assert "train_crop_model" in stages
    assert "fertilizer_artifacts" in stages
    assert "monitor_drift" in stages

    # Check train_crop_model
    train_stage = stages["train_crop_model"]
    assert "--promote" in train_stage["cmd"]
    assert "data/raw/Crop_recommendation.csv" in train_stage["deps"]
    assert "backend/artifacts/crop_model.joblib" in train_stage["outs"]

    # Check fertilizer_artifacts stage uses verification CLI
    fert_stage = stages["fertilizer_artifacts"]
    assert "--verify" in fert_stage["cmd"]
    assert "models/fertilizer_model.joblib" in fert_stage["deps"]

    # Check monitor_drift stage uses synthetic fallback flag
    drift_stage = stages["monitor_drift"]
    assert "--reference" in drift_stage["cmd"]
    assert "--synthetic" in drift_stage["cmd"]

    # Check train_pest_forecasting_v2 stage
    assert "train_pest_forecasting_v2" in stages
    pest_stage = stages["train_pest_forecasting_v2"]
    assert "src.pest_forecasting.train_v2" in pest_stage["cmd"]
    assert "data/experimental/synthetic_pest_forecasting_v2.csv" in pest_stage["deps"]
    assert "src/pest_forecasting/train_v2.py" in pest_stage["deps"]
    assert "backend/ml/model_registry.py" in pest_stage["deps"]
    assert any("environmental_model_pipeline.joblib" in str(out) for out in pest_stage["outs"])
    assert any("full_model_pipeline.joblib" in str(out) for out in pest_stage["outs"])
    assert any("experiment_comparison_summary.json" in str(out) for out in pest_stage["outs"])


def test_fertilizer_artifact_verification(tmp_path):
    summary = verify_fertilizer_artifacts(target_artifacts_dir=tmp_path / "artifacts")
    assert summary["status"] == "VERIFIED"
    assert summary["model_version"] == "1.1.0"
    assert (tmp_path / "artifacts" / "fertilizer_verification.json").exists()
    assert (tmp_path / "artifacts" / "fertilizer_model.joblib").exists()
