from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.ml.drift_monitor import (
    load_reference_data,
    load_prediction_log,
    run_drift_detection,
    get_latest_drift_summary,
    get_drift_history,
)
from backend.ml.prediction_logger import log_prediction_input, count_logged_predictions
from backend.ml.retrain_trigger import should_retrain, get_retrain_history


def test_prediction_logger_roundtrip(tmp_path):
    log_file = tmp_path / "pred_log.jsonl"
    assert count_logged_predictions(log_file) == 0

    log_prediction_input({"N": 90, "P": 42, "K": 43, "temperature": 20.8}, log_path=log_file)
    log_prediction_input({"N": 85, "P": 58, "K": 41, "temperature": 21.7}, log_path=log_file)

    assert count_logged_predictions(log_file) == 2
    df = load_prediction_log(log_file)
    assert len(df) == 2
    assert "N" in df.columns


def test_drift_detection_and_summary(tmp_path):
    ref_df = load_reference_data("data/raw/Crop_recommendation.csv")
    cur_df = load_prediction_log("non_existent_file.jsonl")  # loads synthetic drift sample
    
    report_dir = tmp_path / "drift"
    summary = run_drift_detection(ref_df, cur_df, report_dir=report_dir, run_id="test_run_1")

    assert summary["run_id"] == "test_run_1"
    assert "drift_share" in summary
    assert "drifted_feature_count" in summary
    assert Path(summary["html_report"]).exists()

    latest = get_latest_drift_summary(report_dir)
    assert latest is not None
    assert latest["run_id"] == "test_run_1"

    history = get_drift_history(report_dir)
    assert len(history) == 1
    assert history[0]["run_id"] == "test_run_1"


def test_retrain_decision_logic(tmp_path):
    report_dir = tmp_path / "drift"
    # No reports yet
    should, reason = should_retrain(report_dir)
    assert not should

    # Trigger with alert summary
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_file = report_dir / "drift_summary_alert.json"
    summary_file.write_text(json.dumps({
        "run_id": "alert_run",
        "timestamp": "2026-10-20T12:00:00Z",
        "drift_share": 0.5,
        "drifted_feature_count": 4,
        "alert": True,
    }))
    should, reason = should_retrain(report_dir)
    assert should
    assert "Drift alert" in reason


def test_monitoring_api_endpoints(tmp_path):
    app = create_app(Settings(artifact_dir=tmp_path))
    with TestClient(app) as client:
        # 1. Health snapshot
        res = client.get("/api/v1/monitoring/health")
        assert res.status_code == 200
        data = res.json()
        assert data["mlops_status"] == "ok"
        assert "drift_monitoring" in data
        assert "retraining" in data
        assert "prediction_log" in data

        # 2. Latest drift endpoint
        res = client.get("/api/v1/monitoring/drift/latest")
        assert res.status_code == 200

        # 3. History endpoints
        res = client.get("/api/v1/monitoring/drift/history")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        res = client.get("/api/v1/monitoring/retrain/history")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # 4. Retrain trigger endpoint
        res = client.post("/api/v1/monitoring/retrain/trigger", json={"force": False, "use_mlflow": False})
        assert res.status_code == 200
        assert res.json()["status"] == "queued"
