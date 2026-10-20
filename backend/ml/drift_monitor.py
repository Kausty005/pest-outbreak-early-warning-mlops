"""Evidently AI drift monitor for AgriAdapt crop model inputs."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger(__name__)
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
DRIFT_SHARE_THRESHOLD = 0.3  # fraction of drifted features that triggers an alert


def load_reference_data(dataset_path: str | Path) -> pd.DataFrame:
    """Load training reference dataset, return only feature columns."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Reference dataset not found: {path}")
    df = pd.read_csv(path)
    missing = [f for f in FEATURE_COLUMNS if f not in df.columns]
    if missing:
        raise ValueError(f"Reference dataset missing columns: {missing}")
    return df[FEATURE_COLUMNS]


def load_prediction_log(log_path: str | Path) -> pd.DataFrame:
    """Load logged prediction inputs from a JSONL file."""
    path = Path(log_path)
    if not path.exists() or path.stat().st_size == 0:
        LOGGER.warning("No prediction log at %s — using synthetic drift sample", path)
        return _synthetic_drift_sample()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        return _synthetic_drift_sample()
    df = pd.DataFrame(records)
    return df[[c for c in FEATURE_COLUMNS if c in df.columns]]


def _synthetic_drift_sample(n: int = 200) -> pd.DataFrame:
    """Generate a synthetic batch that simulates moderate input drift (warmer / wetter)."""
    import numpy as np
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "N":           rng.normal(100, 25, n).clip(0, 300),
        "P":           rng.normal(55,  20, n).clip(0, 300),
        "K":           rng.normal(60,  20, n).clip(0, 400),
        "temperature": rng.normal(32,   5, n).clip(-10, 60),  # shifted +5°C vs training
        "humidity":    rng.normal(75,  12, n).clip(0, 100),
        "ph":          rng.normal(6.8, 0.8, n).clip(0, 14),
        "rainfall":    rng.normal(120, 60, n).clip(0, 1000),
    })


def run_drift_detection(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    report_dir: str | Path = "logs/drift",
    run_id: str | None = None,
) -> dict[str, Any]:
    """
    Run Evidently DataDriftPreset on reference vs current data.
    Writes an HTML report + JSON summary and returns the summary dict.
    """
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset

    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc)
    run_id = run_id or ts.strftime("%Y%m%dT%H%M%SZ")

    common_cols = [c for c in FEATURE_COLUMNS if c in reference.columns and c in current.columns]
    ref = reference[common_cols].reset_index(drop=True)
    cur = current[common_cols].reset_index(drop=True)

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)

    html_path = report_dir / f"drift_report_{run_id}.html"
    report.save_html(str(html_path))
    LOGGER.info("Drift HTML report: %s", html_path)

    report_dict = report.as_dict()
    summary: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": ts.isoformat(),
        "reference_rows": len(ref),
        "current_rows": len(cur),
        "features_checked": common_cols,
        "html_report": str(html_path),
        "feature_drift": {},
        "drift_detected": False,
        "drifted_feature_count": 0,
        "drift_share": 0.0,
        "alert": False,
    }

    for metric in report_dict.get("metrics", []):
        result = metric.get("result", {})
        for col, stats in result.get("drift_by_columns", {}).items():
            summary["feature_drift"][col] = {
                "drift_detected": bool(stats.get("drift_detected", False)),
                "stattest": stats.get("stattest_name", ""),
                "p_value": stats.get("p_value"),
                "drift_score": stats.get("drift_score"),
            }
        if "share_of_drifted_columns" in result:
            summary["drift_share"] = float(result["share_of_drifted_columns"])
            summary["drift_detected"] = bool(result.get("dataset_drift", False))
        if "number_of_drifted_columns" in result:
            summary["drifted_feature_count"] = int(result["number_of_drifted_columns"])

    summary["alert"] = summary["drift_share"] >= DRIFT_SHARE_THRESHOLD

    # Persist per-run JSON
    json_path = report_dir / f"drift_summary_{run_id}.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # Append to rolling JSONL log
    rolling = report_dir / "drift_log.jsonl"
    with rolling.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "timestamp": summary["timestamp"],
            "drift_share": summary["drift_share"],
            "drifted_features": summary["drifted_feature_count"],
            "alert": summary["alert"],
        }) + "\n")

    level = logging.WARNING if summary["alert"] else logging.INFO
    LOGGER.log(
        level,
        "Drift complete — share=%.0f%% | drifted=%d/%d | alert=%s",
        summary["drift_share"] * 100,
        summary["drifted_feature_count"],
        len(common_cols),
        summary["alert"],
    )
    return summary


def get_latest_drift_summary(report_dir: str | Path = "logs/drift") -> dict[str, Any] | None:
    """Return the most recent drift summary JSON, or None if no runs yet."""
    summaries = sorted(Path(report_dir).glob("drift_summary_*.json"))
    if not summaries:
        return None
    return json.loads(summaries[-1].read_text(encoding="utf-8"))


def get_drift_history(report_dir: str | Path = "logs/drift", last_n: int = 30) -> list[dict]:
    """Return the last N entries from the rolling drift log."""
    log_path = Path(report_dir) / "drift_log.jsonl"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-last_n:] if line.strip()]

