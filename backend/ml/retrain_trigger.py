"""Retraining trigger for the crop recommendation model.

Reads the latest drift summary. If drift exceeds the threshold,
kicks off a fresh training run and promotes the new model if it
improves on the currently deployed macro F1 score.

Usage:
    python -m backend.ml.retrain_trigger
    python -m backend.ml.retrain_trigger --force
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

RETRAIN_LOG_PATH = Path("logs/retrain_log.jsonl")
DRIFT_REPORT_DIR = Path("logs/drift")
ARTIFACTS_DIR = Path("backend/artifacts")
DATASET_PATH = Path("data/raw/Crop_recommendation.csv")

# Trigger retraining when >= 30% of features drift
DRIFT_ALERT_THRESHOLD = 0.30
# Only promote the new model if macro F1 improves by at least this much
MIN_F1_IMPROVEMENT = 0.001


def _append_retrain_log(record: dict[str, Any]) -> None:
    RETRAIN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RETRAIN_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def get_retrain_history(last_n: int = 20) -> list[dict]:
    if not RETRAIN_LOG_PATH.exists():
        return []
    lines = RETRAIN_LOG_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-last_n:] if line.strip()]


def should_retrain(drift_report_dir: str | Path = DRIFT_REPORT_DIR) -> tuple[bool, str]:
    """
    Return (should_retrain, reason) based on the latest drift summary.
    """
    from backend.ml.drift_monitor import get_latest_drift_summary

    summary = get_latest_drift_summary(drift_report_dir)
    if summary is None:
        return False, "No drift summary available yet — run drift detection first"

    if summary.get("alert"):
        share = summary.get("drift_share", 0.0)
        n = summary.get("drifted_feature_count", 0)
        return True, f"Drift alert: {n} features drifted ({share:.0%} share >= {DRIFT_ALERT_THRESHOLD:.0%} threshold)"

    return False, f"No significant drift — share={summary.get('drift_share', 0):.1%}"


def run_retraining(
    dataset_path: str | Path = DATASET_PATH,
    artifacts_dir: str | Path = ARTIFACTS_DIR,
    use_mlflow: bool = False,
) -> dict[str, Any] | None:
    """
    Execute training via the existing backend.ml.train pipeline.
    Returns the metadata dict on success, None on failure.
    """
    LOGGER.info("Starting retraining from dataset: %s", dataset_path)
    cmd = [
        sys.executable, "-m", "backend.ml.train",
        "--dataset", str(dataset_path),
        "--artifacts-dir", str(artifacts_dir),
        "--quick",   # faster grid search for automated retraining
    ]
    if use_mlflow:
        cmd += ["--mlflow", "--register-mlflow"]

    result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603
    if result.returncode != 0:
        LOGGER.error("Retraining failed:\n%s", result.stderr)
        return None

    try:
        metadata = json.loads(result.stdout)
        LOGGER.info("Retraining complete — version: %s", metadata.get("model_version"))
        return metadata
    except json.JSONDecodeError:
        LOGGER.error("Could not parse training output: %s", result.stdout)
        return None


def maybe_promote(new_metadata: dict[str, Any], artifacts_dir: str | Path = ARTIFACTS_DIR) -> bool:
    """
    Promote the new model if it improves on the current champion.
    Returns True if promoted.
    """
    from backend.ml.model_registry import promote_candidate, PromotionError

    try:
        promote_candidate(
            artifacts_dir,
            new_metadata,
            min_macro_f1_improvement=MIN_F1_IMPROVEMENT,
        )
        LOGGER.info(
            "Promoted new model %s to production",
            new_metadata.get("model_version"),
        )
        return True
    except PromotionError as exc:
        LOGGER.warning("Promotion skipped: %s", exc)
        return False


def run_trigger(
    force: bool = False,
    drift_report_dir: str | Path = DRIFT_REPORT_DIR,
    dataset_path: str | Path = DATASET_PATH,
    artifacts_dir: str | Path = ARTIFACTS_DIR,
    use_mlflow: bool = False,
) -> dict[str, Any]:
    """
    Full retrain-trigger lifecycle:
      1. Check drift
      2. If alert (or forced), retrain
      3. Attempt promotion
      4. Write retrain log entry
    Returns a summary dict.
    """
    ts = datetime.now(timezone.utc).isoformat()
    triggered, reason = should_retrain(drift_report_dir)

    if not triggered and not force:
        summary = {"timestamp": ts, "triggered": False, "reason": reason}
        LOGGER.info("Retrain not triggered: %s", reason)
        _append_retrain_log(summary)
        return summary

    LOGGER.info("Retrain triggered: %s", reason)
    new_metadata = run_retraining(dataset_path, artifacts_dir, use_mlflow)

    if new_metadata is None:
        summary = {
            "timestamp": ts,
            "triggered": True,
            "reason": reason,
            "retrain_succeeded": False,
            "promoted": False,
        }
        _append_retrain_log(summary)
        return summary

    promoted = maybe_promote(new_metadata, artifacts_dir)
    summary = {
        "timestamp": ts,
        "triggered": True,
        "reason": reason,
        "retrain_succeeded": True,
        "new_model_version": new_metadata.get("model_version"),
        "new_macro_f1": new_metadata.get("evaluation_metrics", {}).get("macro_f1"),
        "promoted": promoted,
    }
    _append_retrain_log(summary)
    return summary


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Check drift and retrain if needed")
    parser.add_argument("--force", action="store_true", help="Force retraining regardless of drift")
    parser.add_argument("--mlflow", action="store_true", help="Log run to MLflow")
    args = parser.parse_args()
    result = run_trigger(force=args.force, use_mlflow=args.mlflow)
    print(json.dumps(result, indent=2))
