"""
backend/ml/pest_retrain_trigger.py
──────────────────────────────────
Controlled automated retraining trigger and gate verification for
Version 2.0 Pest Outbreak Forecasting.

SCIENTIFIC & MLOps INVARIANTS:
1. Reuses the project's trigger and readiness gate architecture.
2. Prevents retraining on invalid, insufficient, or synthetic data presented as authentic.
3. Supervised production retraining is strictly BLOCKED until authentic field surveillance
   satisfies all 11 scientific readiness criteria (>=500 multi-season observations).
4. Experimental retraining evaluates candidates against PR-AUC thresholds and SHA-256 manifests.
5. Strictly enforces experimental tier isolation; never promotes to production.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.ml.model_registry import (
    promote_pest_experimental_candidate,
    read_pest_ledger,
    stage_pest_candidate,
    validate_pest_candidate,
)
from src.pest_risk.production_readiness_gate import (
    MINIMUM_AUTHENTIC_RECORDS,
    MINIMUM_POSITIVE_LABELS,
    evaluate_production_readiness,
)

LOGGER = logging.getLogger(__name__)

PEST_RETRAIN_LOG_PATH = Path("logs/pest_retrain_log.jsonl")
MODELS_DIR = Path("models/experimental_synthetic_pest_v2")
EXPERIMENTAL_DATASET_PATH = Path("data/experimental/synthetic_pest_forecasting_v2.csv")


def _append_pest_retrain_log(record: dict[str, Any]) -> None:
    """Safely append an audit record to the pest retrain log."""
    PEST_RETRAIN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PEST_RETRAIN_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def get_pest_retrain_history(last_n: int = 20) -> list[dict[str, Any]]:
    """Retrieve the last N pest retrain event records."""
    if not PEST_RETRAIN_LOG_PATH.exists():
        return []
    lines = PEST_RETRAIN_LOG_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-last_n:] if line.strip()]


def check_pest_retraining_eligibility() -> tuple[bool, str, dict[str, Any]]:
    """
    Evaluate whether preconditions for supervised retraining are met.

    Strictly inspects:
    1. Production readiness gate (all 11 criteria).
    2. Authentic field observation counts (>= 500).
    3. Positive outbreak event sufficiency (>= 50).
    4. Absence of synthetic data masquerading as authentic field records.
    """
    readiness_report = evaluate_production_readiness()

    meta = {
        "gate_status": readiness_report.gate_status,
        "is_ready_for_training": readiness_report.is_ready_for_training,
        "authentic_records_found": readiness_report.data_foundation_inventory.get("authentic_field_observations_count", 0),
        "minimum_required": MINIMUM_AUTHENTIC_RECORDS,
        "blocking_reasons": readiness_report.blocking_reasons,
    }

    if readiness_report.gate_status == "BLOCKED":
        primary_reason = readiness_report.blocking_reasons[0] if readiness_report.blocking_reasons else "Readiness gate blocked."
        return False, f"Retraining blocked by Scientific Readiness Gate: {primary_reason}", meta

    return True, "All scientific readiness criteria satisfied for authentic field retraining.", meta


def trigger_controlled_pest_retraining(
    force_experimental: bool = False,
    dataset_path: str | Path = EXPERIMENTAL_DATASET_PATH,
    models_dir: str | Path = MODELS_DIR,
    use_mlflow: bool = False,
) -> dict[str, Any]:
    """
    Execute controlled pest retraining pipeline.

    - If production retraining is requested: enforces readiness gate checks.
    - If force_experimental=True: executes experimental pipeline update on verified experimental dataset,
      stages candidate, validates PR-AUC gates and SHA-256 integrity, backs up previous version,
      and records promotion in pest deployment ledger.
    """
    dataset_p = Path(dataset_path)
    models_p = Path(models_dir)
    now_iso = datetime.now(timezone.utc).isoformat()

    eligible, reason, meta = check_pest_retraining_eligibility()

    if not eligible and not force_experimental:
        audit_record = {
            "timestamp": now_iso,
            "status": "REJECTED_BY_READINESS_GATE",
            "reason": reason,
            "metadata": meta,
            "retraining_executed": False,
        }
        _append_pest_retrain_log(audit_record)
        LOGGER.warning("Controlled pest retraining request rejected: %s", reason)
        return audit_record

    # Verify dataset existence
    if not dataset_p.exists():
        audit_record = {
            "timestamp": now_iso,
            "status": "FAILED_DATASET_NOT_FOUND",
            "reason": f"Dataset file does not exist at {dataset_p}",
            "retraining_executed": False,
        }
        _append_pest_retrain_log(audit_record)
        return audit_record

    LOGGER.info("Starting controlled experimental pest retraining from %s", dataset_p)

    cmd = [
        sys.executable, "-m", "src.pest_forecasting.train_v2",
        "--dataset", str(dataset_p),
        "--models-dir", str(models_p),
        "--quick",
    ]
    if use_mlflow:
        cmd += ["--mlflow"]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        audit_record = {
            "timestamp": now_iso,
            "status": "TRAINING_FAILED",
            "reason": proc.stderr.strip() or proc.stdout.strip(),
            "retraining_executed": False,
        }
        _append_pest_retrain_log(audit_record)
        LOGGER.error("Pest retraining execution failed:\n%s", proc.stderr)
        return audit_record

    # Parse training summary
    try:
        summary_file = models_p / "experiment_comparison_summary.json"
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
    except Exception as exc:
        summary = {"error": str(exc)}

    # Stage candidate in model registry
    timestamp_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate_version = f"pest-v2-{timestamp_tag}-retrained"

    try:
        summary["model_version"] = candidate_version
        cand_dir = stage_pest_candidate(
            models_dir=models_p,
            version=candidate_version,
            candidate_metadata=summary,
            source_artifacts_dir=models_p,
        )

        ledger = read_pest_ledger(models_p)

        # Validate candidate via registry promotion gate
        is_valid, gate_reason = validate_pest_candidate(
            candidate_metadata=summary,
            candidate_dir=cand_dir,
            current_ledger=ledger,
            min_val_pr_auc=0.50,
            target_tier="experimental",  # Synthetic models can ONLY be experimental
        )

        if not is_valid:
            audit_record = {
                "timestamp": now_iso,
                "status": "CANDIDATE_GATE_REJECTED",
                "candidate_version": candidate_version,
                "gate_errors": [gate_reason],
                "retraining_executed": True,
                "promoted": False,
            }
            _append_pest_retrain_log(audit_record)
            return audit_record

        # Promote experimental candidate with automatic backup of previous artifacts
        ledger_entry = promote_pest_experimental_candidate(
            models_dir=models_p,
            candidate_metadata=summary,
            candidate_source_dir=cand_dir,
            min_val_pr_auc=0.50,
            target_tier="experimental",
        )

        audit_record = {
            "timestamp": now_iso,
            "status": "SUCCESS_EXPERIMENTAL_PROMOTED",
            "candidate_version": candidate_version,
            "ledger_entry": ledger_entry,
            "retraining_executed": True,
            "promoted": True,
            "target_tier": "experimental",
            "is_production_ready": False,
        }
        _append_pest_retrain_log(audit_record)
        LOGGER.info("Pest candidate %s successfully validated and promoted to experimental tier.", candidate_version)
        return audit_record

    except Exception as exc:
        LOGGER.exception("Error during candidate registration or promotion: %s", exc)
        audit_record = {
            "timestamp": now_iso,
            "status": "REGISTRY_ERROR",
            "error": str(exc),
            "retraining_executed": True,
            "promoted": False,
        }
        _append_pest_retrain_log(audit_record)
        return audit_record
