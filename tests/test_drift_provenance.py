from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from backend.ml.data_validation import FEATURE_COLUMNS
from backend.ml.drift_monitor import (
    load_prediction_log,
    load_reference_data,
    run_drift_detection,
)


def test_malformed_jsonl_lines_handled_safely(tmp_path):
    log_file = tmp_path / "preds.jsonl"
    lines = [
        json.dumps({"N": 90, "P": 40, "K": 40, "temperature": 25, "humidity": 70, "ph": 6.5, "rainfall": 150}),
        "THIS IS NOT VALID JSON {[[",
        "",
        json.dumps({"N": 85, "P": 45, "K": 42, "temperature": 26, "humidity": 72, "ph": 6.6, "rainfall": 140}),
        json.dumps({"N": 80, "P": 42, "K": 41, "temperature": 27, "humidity": 75, "ph": 6.4, "rainfall": 160}),
        json.dumps({"N": 88, "P": 48, "K": 39, "temperature": 24, "humidity": 68, "ph": 6.7, "rainfall": 130}),
        json.dumps({"N": 92, "P": 50, "K": 44, "temperature": 28, "humidity": 80, "ph": 6.3, "rainfall": 170}),
    ]
    log_file.write_text("\n".join(lines), encoding="utf-8")

    df = load_prediction_log(log_file, allow_synthetic=False, min_samples=5)
    assert len(df) == 5
    assert df.attrs["data_source"] == "production_logs"
    assert df.attrs["is_synthetic"] is False


def test_empty_log_rejection_without_synthetic_flag(tmp_path):
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Insufficient production samples"):
        load_prediction_log(empty_file, allow_synthetic=False, min_samples=5)


def test_synthetic_fallback_labeled_explicitly(tmp_path):
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")

    df = load_prediction_log(empty_file, allow_synthetic=True, min_samples=5)
    assert len(df) == 200
    assert df.attrs["data_source"] == "synthetic_demonstration"
    assert df.attrs["is_synthetic"] is True


def test_drift_detection_provenance_and_constant_columns(tmp_path):
    # Reference and current dataframe
    ref_data = {col: [50.0] * 30 for col in FEATURE_COLUMNS}
    cur_data = {col: [50.0] * 30 for col in FEATURE_COLUMNS}
    ref_df = pd.DataFrame(ref_data)
    cur_df = pd.DataFrame(cur_data)
    cur_df.attrs["data_source"] = "production_logs"
    cur_df.attrs["is_synthetic"] = False

    report_dir = tmp_path / "drift_out"
    summary = run_drift_detection(ref_df, cur_df, report_dir=report_dir, run_id="constant_test")

    assert summary["data_source"] == "production_logs"
    assert summary["is_synthetic"] is False
    assert summary["drift_share"] == 0.0
    assert summary["alert"] is False
    assert Path(summary["html_report"]).exists()
    assert summary["performance_degradation_measured"] is False
    assert "performance_degradation_note" in summary


def test_retrain_trigger_ignores_synthetic_alert(tmp_path):
    from backend.ml.retrain_trigger import should_retrain

    report_dir = tmp_path / "drift"
    report_dir.mkdir(parents=True)
    summary_file = report_dir / "drift_summary_synthetic.json"
    summary_file.write_text(
        json.dumps({
            "run_id": "synth_run_1",
            "timestamp": "2026-10-27T12:00:00Z",
            "is_synthetic": True,
            "data_source": "synthetic_demonstration",
            "alert": True,
            "drift_share": 0.8,
            "drifted_feature_count": 6,
        }),
        encoding="utf-8",
    )
    should, reason = should_retrain(report_dir)
    assert not should
    assert "synthetic demonstration data" in reason

