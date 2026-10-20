"""Small file-backed promotion ledger for local development and explicit rollback."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class PromotionError(ValueError):
    pass


def _ledger_path(artifact_dir: str | Path) -> Path:
    return Path(artifact_dir) / "deployment_ledger.json"


def read_ledger(artifact_dir: str | Path) -> dict:
    path = _ledger_path(artifact_dir)
    if not path.exists():
        return {"production_version": None, "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def promote_candidate(
    artifact_dir: str | Path,
    candidate_metadata: dict,
    min_macro_f1_improvement: float = 0.0,
) -> dict:
    """Promote only after an explicit call and an auditable metric comparison."""
    candidate_f1 = float(candidate_metadata["evaluation_metrics"]["macro_f1"])
    ledger = read_ledger(artifact_dir)
    deployed_f1 = ledger.get("production_macro_f1")
    if deployed_f1 is not None and candidate_f1 < float(deployed_f1) + min_macro_f1_improvement:
        raise PromotionError(
            f"Candidate macro F1 {candidate_f1:.4f} does not meet required improvement over {deployed_f1:.4f}"
        )
    version = candidate_metadata["model_version"]
    ledger["production_version"] = version
    ledger["production_macro_f1"] = candidate_f1
    ledger.setdefault("history", []).append(
        {
            "action": "promote",
            "model_version": version,
            "macro_f1": candidate_f1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    _ledger_path(artifact_dir).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return ledger


def rollback(artifact_dir: str | Path, target_version: str, target_macro_f1: float) -> dict:
    """Record an explicit rollback. Artifact deployment remains an operator action."""
    ledger = read_ledger(artifact_dir)
    ledger["production_version"] = target_version
    ledger["production_macro_f1"] = float(target_macro_f1)
    ledger.setdefault("history", []).append(
        {
            "action": "rollback",
            "model_version": target_version,
            "macro_f1": float(target_macro_f1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    _ledger_path(artifact_dir).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return ledger
