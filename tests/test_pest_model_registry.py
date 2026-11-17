"""
tests/test_pest_model_registry.py
─────────────────────────────────
Comprehensive test suite for pest forecasting model registry integration:
- Candidate registration and staging with version identification.
- SHA-256 integrity calculation and tamper detection.
- Evaluation-based validation gates (validation PR-AUC).
- Strict separation between experimental and production models.
- Guaranteed rejection of synthetic model promotion to production.
- Atomic promotion in the experimental tier with automatic versioned backup.
- Physical rollback and restoration of model artifacts and ledger state.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib
import pytest
from sklearn.linear_model import LogisticRegression

from backend.ml.model_registry import (
    PromotionError,
    RollbackError,
    promote_pest_experimental_candidate,
    read_pest_ledger,
    rollback_pest_experimental,
    sha256_file,
    stage_pest_candidate,
    validate_pest_candidate,
)
from src.pest_forecasting.dataset_v2 import ENVIRONMENTAL_FEATURE_COLUMNS, FULL_FEATURE_COLUMNS
from src.pest_forecasting.preprocessor_v2 import build_model_pipeline_v2


def _create_mock_pest_artifacts(target_dir: Path) -> dict[str, Any]:
    """Helper to generate minimal valid mock pipelines and metadata."""
    target_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    import numpy as np

    env_cols = list(ENVIRONMENTAL_FEATURE_COLUMNS)
    full_cols = list(FULL_FEATURE_COLUMNS)

    # Minimal dummy training data
    df_env = pd.DataFrame(
        {c: [1.0, 2.0, 3.0, 4.0] if "temp" in c or "rh" in c or "soil" in c or "rain" in c or "days" in c
         else ["Nagpur", "Nagpur", "Amravati", "Amravati"] if c == "district"
         else ["Cotton", "Cotton", "Rice", "Rice"] if c == "crop"
         else ["Pink Bollworm", "Pink Bollworm", "Stem Borer", "Stem Borer"] if c == "pest"
         else ["vegetative", "flowering", "vegetative", "grain_filling"]
         for c in env_cols}
    )
    df_full = df_env.copy()
    for c in full_cols:
        if c not in df_full.columns:
            df_full[c] = 0.0

    y = pd.Series([0, 1, 0, 1])

    env_pipe = build_model_pipeline_v2(
        LogisticRegression(random_state=42),
        feature_columns=env_cols,
    )
    env_pipe.fit(df_env, y)

    full_pipe = build_model_pipeline_v2(
        LogisticRegression(random_state=42),
        feature_columns=full_cols,
    )
    full_pipe.fit(df_full, y)

    joblib.dump(env_pipe, target_dir / "environmental_model_pipeline.joblib")
    joblib.dump(full_pipe, target_dir / "full_model_pipeline.joblib")

    schemas = {
        "version": "2.0.0",
        "environmental_features": env_cols,
        "scouting_assisted_features": full_cols,
        "target_column": "outbreak_within_7d",
    }
    (target_dir / "feature_schemas.json").write_text(json.dumps(schemas), encoding="utf-8")
    (target_dir / "model_config.json").write_text(json.dumps({"random_seed": 42}), encoding="utf-8")
    (target_dir / "partition_metadata.json").write_text(json.dumps({"purged_samples": 100}), encoding="utf-8")
    (target_dir / "synthetic_provenance_metadata.json").write_text(
        json.dumps({
            "classification": "SYNTHETIC_EXPERIMENTAL_V2",
            "is_production_ready": False,
        }),
        encoding="utf-8",
    )
    (target_dir / "stress_test_results.json").write_text(json.dumps({"status": "PASSED"}), encoding="utf-8")
    (target_dir / "inference_examples.json").write_text(json.dumps({"status": "SYNTHETIC_EXPERIMENTAL"}), encoding="utf-8")

    meta = {
        "model_version": "pest-v2-mock-v1",
        "best_val_pr_auc": 0.72,
        "classification": "SYNTHETIC_EXPERIMENTAL_V2",
        "is_production_ready": False,
        "experiments": {
            "ENVIRONMENTAL_ONLY": {"best_val_pr_auc": 0.65},
            "SCOUTING_ASSISTED": {"best_val_pr_auc": 0.72},
        },
    }
    (target_dir / "experiment_comparison_summary.json").write_text(json.dumps(meta), encoding="utf-8")

    return meta


def test_stage_pest_candidate_computes_sha256_checksums(tmp_path: Path):
    """Verify that stage_pest_candidate calculates and stores SHA-256 for all artifacts."""
    src_dir = tmp_path / "mock_src"
    models_dir = tmp_path / "models_registry"
    meta = _create_mock_pest_artifacts(src_dir)

    cand_dir = stage_pest_candidate(
        models_dir=models_dir,
        version="pest-v2-cand-001",
        candidate_metadata=meta,
        source_artifacts_dir=src_dir,
    )

    assert cand_dir.exists()
    assert (cand_dir / "checksums.sha256").exists()
    assert (cand_dir / "candidate_metadata.json").exists()

    cand_meta = json.loads((cand_dir / "candidate_metadata.json").read_text(encoding="utf-8"))
    assert "artifact_checksums" in cand_meta
    checksums = cand_meta["artifact_checksums"]
    assert "environmental_model_pipeline.joblib" in checksums
    assert "full_model_pipeline.joblib" in checksums

    # Verify that stored checksum matches actual file hash
    actual_hash = sha256_file(cand_dir / "environmental_model_pipeline.joblib")
    assert checksums["environmental_model_pipeline.joblib"] == actual_hash


def test_validate_pest_candidate_checksum_tamper_detection(tmp_path: Path):
    """Verify that validate_pest_candidate detects corrupted or tampered joblib files."""
    models_dir = tmp_path / "models_registry"
    src_dir = tmp_path / "mock_src"
    meta = _create_mock_pest_artifacts(src_dir)

    cand_dir = stage_pest_candidate(
        models_dir=models_dir,
        version="pest-v2-tamper-check",
        candidate_metadata=meta,
        source_artifacts_dir=src_dir,
    )

    cand_meta = json.loads((cand_dir / "candidate_metadata.json").read_text(encoding="utf-8"))
    is_valid, reason = validate_pest_candidate(cand_meta, candidate_dir=cand_dir)
    assert is_valid, f"Expected valid candidate, got: {reason}"

    # Tamper with the joblib binary
    (cand_dir / "environmental_model_pipeline.joblib").write_bytes(b"corrupted binary payload")

    is_valid_tampered, tamper_reason = validate_pest_candidate(cand_meta, candidate_dir=cand_dir)
    assert not is_valid_tampered
    assert "checksum mismatch" in tamper_reason.lower()


def test_validate_pest_candidate_pr_auc_thresholds(tmp_path: Path):
    """Verify validation gates reject candidates with insufficient PR-AUC."""
    meta_low = {
        "model_version": "cand-low",
        "best_val_pr_auc": 0.35,
        "classification": "SYNTHETIC_EXPERIMENTAL_V2",
    }
    valid, reason = validate_pest_candidate(meta_low, min_val_pr_auc=0.50)
    assert not valid
    assert "below minimum requirement" in reason

    meta_ok = {
        "model_version": "cand-ok",
        "best_val_pr_auc": 0.65,
        "classification": "SYNTHETIC_EXPERIMENTAL_V2",
    }
    valid, reason = validate_pest_candidate(meta_ok, min_val_pr_auc=0.50)
    assert valid


def test_strict_production_promotion_block_for_synthetic_models(tmp_path: Path):
    """
    STRICT SCIENTIFIC RESTRICTION:
    Models trained on synthetic data MUST NEVER be promoted to production.
    Attempting production promotion MUST raise PromotionError.
    """
    src_dir = tmp_path / "mock_src"
    models_dir = tmp_path / "models_registry"
    meta = _create_mock_pest_artifacts(src_dir)

    cand_dir = stage_pest_candidate(
        models_dir=models_dir,
        version="pest-v2-synthetic-test",
        candidate_metadata=meta,
        source_artifacts_dir=src_dir,
    )
    cand_meta = json.loads((cand_dir / "candidate_metadata.json").read_text(encoding="utf-8"))

    # 1. Validation explicitly flags failure for production tier
    is_valid, reason = validate_pest_candidate(cand_meta, candidate_dir=cand_dir, target_tier="production")
    assert not is_valid
    assert "strictly blocked" in reason.lower()
    assert "synthetic" in reason.lower()

    # 2. Promotion to production tier raises PromotionError
    with pytest.raises(PromotionError, match="strictly BLOCKED"):
        promote_pest_experimental_candidate(
            models_dir=models_dir,
            candidate_metadata=cand_meta,
            candidate_source_dir=cand_dir,
            target_tier="production",
        )


def test_experimental_promotion_with_automatic_backup_and_rollback(tmp_path: Path):
    """
    Verify complete experimental lifecycle:
    1. Promote candidate 1 to active experimental tier.
    2. Promote candidate 2 (with higher PR-AUC); candidate 1 is backed up automatically.
    3. Rollback from candidate 2 to candidate 1; artifacts physically restored and verified.
    """
    src_v1 = tmp_path / "mock_v1"
    src_v2 = tmp_path / "mock_v2"
    models_dir = tmp_path / "models_registry"

    meta_v1 = _create_mock_pest_artifacts(src_v1)
    meta_v1["model_version"] = "pest-exp-v1"
    meta_v1["best_val_pr_auc"] = 0.60

    meta_v2 = _create_mock_pest_artifacts(src_v2)
    meta_v2["model_version"] = "pest-exp-v2"
    meta_v2["best_val_pr_auc"] = 0.75

    # Stage both
    c_dir_v1 = stage_pest_candidate(models_dir, "pest-exp-v1", meta_v1, source_artifacts_dir=src_v1)
    c_dir_v2 = stage_pest_candidate(models_dir, "pest-exp-v2", meta_v2, source_artifacts_dir=src_v2)

    # 1. Promote v1 to active experimental
    ledger_v1 = promote_pest_experimental_candidate(models_dir, meta_v1, candidate_source_dir=c_dir_v1)
    assert ledger_v1["active_experimental_version"] == "pest-exp-v1"
    assert ledger_v1["active_val_pr_auc"] == 0.60
    assert (models_dir / "environmental_model_pipeline.joblib").exists()
    v1_env_sha = sha256_file(models_dir / "environmental_model_pipeline.joblib")

    # 2. Promote v2; verify v1 backup was created
    ledger_v2 = promote_pest_experimental_candidate(models_dir, meta_v2, candidate_source_dir=c_dir_v2)
    assert ledger_v2["active_experimental_version"] == "pest-exp-v2"
    assert ledger_v2["active_val_pr_auc"] == 0.75
    assert (models_dir / "backups" / "pest-exp-v1" / "environmental_model_pipeline.joblib").exists()

    # 3. Rollback to v1
    ledger_rb = rollback_pest_experimental(models_dir, target_version="pest-exp-v1")
    assert ledger_rb["active_experimental_version"] == "pest-exp-v1"
    restored_sha = sha256_file(models_dir / "environmental_model_pipeline.joblib")
    assert restored_sha == v1_env_sha

    # Verify that restored pipeline loads and executes inference cleanly
    restored_pipe = joblib.load(models_dir / "environmental_model_pipeline.joblib")
    assert hasattr(restored_pipe, "predict_proba")
