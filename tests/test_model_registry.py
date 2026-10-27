from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest
from sklearn.ensemble import RandomForestClassifier

from backend.ml.data_validation import FEATURE_COLUMNS
from backend.ml.feature_engineering import FeatureConfig, make_model_pipeline
from backend.ml.model_registry import (
    DEFAULT_MIN_MACRO_F1,
    PromotionError,
    PromotionLock,
    RollbackError,
    promote_candidate,
    read_ledger,
    rollback,
    sha256_file,
    stage_candidate,
    validate_candidate,
)


def _dummy_pipeline(synthetic_frame, n_est=5):
    pipe = make_model_pipeline(
        RandomForestClassifier(n_estimators=n_est, random_state=42),
        FeatureConfig(enabled=False),
    )
    pipe.fit(synthetic_frame[FEATURE_COLUMNS], synthetic_frame["label"])
    return pipe


def test_validate_candidate_thresholds():
    # Missing version
    valid, reason = validate_candidate({})
    assert not valid
    assert "model_version" in reason

    # Low F1
    meta = {"model_version": "v1", "evaluation_metrics": {"macro_f1": 0.70}}
    valid, reason = validate_candidate(meta, min_macro_f1=0.85)
    assert not valid
    assert "below minimum" in reason

    # Below deployed F1
    ledger = {"production_macro_f1": 0.95}
    meta_good = {"model_version": "v2", "evaluation_metrics": {"macro_f1": 0.92}}
    valid, reason = validate_candidate(meta_good, current_ledger=ledger, min_macro_f1=0.85, min_macro_f1_improvement=0.01)
    assert not valid
    assert "does not meet required improvement" in reason

    # Superior candidate
    meta_better = {"model_version": "v3", "evaluation_metrics": {"macro_f1": 0.98}}
    valid, reason = validate_candidate(meta_better, current_ledger=ledger, min_macro_f1=0.85, min_macro_f1_improvement=0.01)
    assert valid


def test_staging_does_not_overwrite_production(tmp_path, synthetic_frame):
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    prod_joblib = art_dir / "crop_model.joblib"
    prod_joblib.write_text("original production artifact")

    pipeline = _dummy_pipeline(synthetic_frame)
    meta = {"model_version": "cand-1", "evaluation_metrics": {"macro_f1": 0.92}}
    c_dir = stage_candidate(art_dir, pipeline, meta, evaluation_report_md="# Cand 1")

    assert c_dir.exists()
    assert (c_dir / "crop_model.joblib").exists()
    # Verify production artifact was NOT modified
    assert prod_joblib.read_text() == "original production artifact"


def test_atomic_promotion_and_physical_rollback(tmp_path, synthetic_frame):
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()

    pipe_v1 = _dummy_pipeline(synthetic_frame, n_est=5)
    meta_v1 = {
        "model_version": "crop-v1",
        "evaluation_metrics": {"macro_f1": 0.90, "accuracy": 0.90},
    }
    c_dir_v1 = stage_candidate(art_dir, pipe_v1, meta_v1)
    promote_candidate(art_dir, meta_v1, candidate_source_dir=c_dir_v1)

    ledger = read_ledger(art_dir)
    assert ledger["production_version"] == "crop-v1"
    assert ledger["production_macro_f1"] == 0.90
    assert (art_dir / "crop_model.joblib").exists()
    v1_sha = sha256_file(art_dir / "crop_model.joblib")

    # Reject inferior candidate v2
    pipe_v2 = _dummy_pipeline(synthetic_frame, n_est=10)
    meta_v2 = {
        "model_version": "crop-v2-inferior",
        "evaluation_metrics": {"macro_f1": 0.88, "accuracy": 0.88},
    }
    c_dir_v2 = stage_candidate(art_dir, pipe_v2, meta_v2)
    with pytest.raises(PromotionError):
        promote_candidate(art_dir, meta_v2, candidate_source_dir=c_dir_v2)

    # Production is still v1
    assert read_ledger(art_dir)["production_version"] == "crop-v1"
    assert sha256_file(art_dir / "crop_model.joblib") == v1_sha

    # Promote superior candidate v3
    meta_v3 = {
        "model_version": "crop-v3-superior",
        "evaluation_metrics": {"macro_f1": 0.95, "accuracy": 0.95},
    }
    c_dir_v3 = stage_candidate(art_dir, pipe_v2, meta_v3)
    promote_candidate(art_dir, meta_v3, candidate_source_dir=c_dir_v3)

    assert read_ledger(art_dir)["production_version"] == "crop-v3-superior"
    assert (art_dir / "backups" / "crop-v1" / "crop_model.joblib").exists()

    # Now execute physical rollback to crop-v1
    rollback(art_dir, target_version="crop-v1")
    ledger_after_rb = read_ledger(art_dir)
    assert ledger_after_rb["production_version"] == "crop-v1"
    assert ledger_after_rb["production_macro_f1"] == 0.90
    assert sha256_file(art_dir / "crop_model.joblib") == v1_sha

    # Verify restored model loads and predicts cleanly
    restored_pipeline = joblib.load(art_dir / "crop_model.joblib")
    preds = restored_pipeline.predict(synthetic_frame[FEATURE_COLUMNS].head(2))
    assert len(preds) == 2


def test_rollback_missing_backup_raises_error(tmp_path):
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    with pytest.raises(RollbackError):
        rollback(art_dir, target_version="non-existent-version")


def test_candidate_rejection_invalid_checksum(tmp_path):
    model_file = tmp_path / "crop_model.joblib"
    model_file.write_text("dummy model content")
    meta = {
        "model_version": "cand-checksum-fail",
        "evaluation_metrics": {"macro_f1": 0.95},
        "artifact_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    is_valid, reason = validate_candidate(meta, candidate_joblib_path=model_file)
    assert not is_valid
    assert "checksum mismatch" in reason.lower()


def test_promotion_lock_blocks_concurrent_promotion(tmp_path):
    lock_file = tmp_path / ".promotion.lock"
    with PromotionLock(lock_file, timeout=0.2):
        # Attempting second acquisition while lock is held must raise RuntimeError
        with pytest.raises(RuntimeError, match="Could not acquire promotion lock"):
            with PromotionLock(lock_file, timeout=0.2):
                pass
    # After exiting, lock must be released and re-acquirable
    with PromotionLock(lock_file, timeout=0.2):
        assert lock_file.exists()
    assert not lock_file.exists()


def test_promotion_failure_leaves_production_intact(tmp_path, synthetic_frame):
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    prod_joblib = art_dir / "crop_model.joblib"
    prod_meta = art_dir / "metadata.json"
    prod_joblib.write_text("initial production binary")
    prod_meta.write_text(json.dumps({"model_version": "prod-v0", "production_macro_f1": 0.92}))

    # Candidate with corrupted/failing metrics
    c_dir = art_dir / "candidates" / "bad-cand"
    c_dir.mkdir(parents=True)
    (c_dir / "crop_model.joblib").write_text("candidate binary")
    bad_meta = {"model_version": "bad-cand", "evaluation_metrics": {"macro_f1": 0.50}}

    with pytest.raises(PromotionError):
        promote_candidate(art_dir, bad_meta, candidate_source_dir=c_dir)

    # Production remains unchanged
    assert prod_joblib.read_text() == "initial production binary"
    assert json.loads(prod_meta.read_text())["model_version"] == "prod-v0"
    # No dangling .tmp files
    assert not (art_dir / "crop_model.joblib.tmp").exists()
    assert not (art_dir / "metadata.json.tmp").exists()
