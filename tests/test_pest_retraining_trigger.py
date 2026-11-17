"""
tests/test_pest_retraining_trigger.py
─────────────────────────────────────
Verification tests for the controlled pest forecasting retraining trigger:
- Gating against insufficient/synthetic surveillance data.
- Refusal logging to logs/pest_retrain_log.jsonl.
- Authorized experimental retraining execution, candidate staging, and promotion.
- Strict isolation from production.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.ml.pest_retrain_trigger import (
    PEST_RETRAIN_LOG_PATH,
    check_pest_retraining_eligibility,
    get_pest_retrain_history,
    trigger_controlled_pest_retraining,
)

client = TestClient(app)


def test_pest_retraining_eligibility_blocks_when_insufficient_records():
    """Verify retraining eligibility evaluates to False when authentic records < 500."""
    eligible, reason, meta = check_pest_retraining_eligibility()
    assert eligible is False
    assert "Scientific Readiness Gate" in reason
    assert meta["gate_status"] == "BLOCKED"
    assert meta["minimum_required"] == 500


def test_api_pest_retrain_status_endpoint():
    """Verify GET /api/v1/monitoring/pest-retrain/status endpoint."""
    resp = client.get("/api/v1/monitoring/pest-retrain/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible_for_authentic_retraining"] is False
    assert "readiness_summary" in data
    assert data["readiness_summary"]["gate_status"] == "BLOCKED"


def test_api_pest_retrain_trigger_blocks_unauthorized_production_attempt(tmp_path: Path):
    """Verify POST /api/v1/monitoring/pest-retrain/trigger rejects attempts without force_experimental."""
    resp = client.post("/api/v1/monitoring/pest-retrain/trigger", json={"force_experimental": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert "Scientific Readiness Gate" in data["reason"]

    # Verify audit record is present in history
    history_resp = client.get("/api/v1/monitoring/pest-retrain/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) > 0
    latest = history[-1]
    assert latest["status"] == "REJECTED_BY_READINESS_GATE"
    assert latest["retraining_executed"] is False


def test_controlled_experimental_retraining_workflow(tmp_path: Path):
    """
    Verify controlled experimental retraining workflow:
    - Runs training on experimental dataset in quick mode.
    - Stages candidate in registry.
    - Validates PR-AUC gates and SHA-256 integrity.
    - Backs up previous version and promotes to experimental tier.
    - Strict isolation: target tier is experimental, never production.
    """
    dest_models_dir = tmp_path / "models_retrain_test"
    dest_models_dir.mkdir(parents=True, exist_ok=True)

    # Initial copy of current experimental model files into tmp_path (excluding baseline ledger)
    source_dir = Path("models/experimental_synthetic_pest_v2")
    for f in source_dir.glob("*.*"):
        if f.name != "pest_deployment_ledger.json":
            (dest_models_dir / f.name).write_bytes(f.read_bytes())

    res = trigger_controlled_pest_retraining(
        force_experimental=True,
        models_dir=dest_models_dir,
    )

    assert res["retraining_executed"] is True
    assert res["status"] == "SUCCESS_EXPERIMENTAL_PROMOTED"
    assert res["promoted"] is True
    assert res["target_tier"] == "experimental"
    assert res["is_production_ready"] is False
    assert "candidate_version" in res
    assert "pest-v2-" in res["candidate_version"]
