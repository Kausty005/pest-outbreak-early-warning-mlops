"""MLOps monitoring API — drift status, drift history, retrain trigger.

Endpoints:
    GET  /api/v1/monitoring/drift/latest     → most recent drift summary
    GET  /api/v1/monitoring/drift/history    → last N drift runs (sparkline data)
    GET  /api/v1/monitoring/retrain/history  → last N retrain events
    POST /api/v1/monitoring/drift/run        → run drift detection now
    POST /api/v1/monitoring/retrain/trigger  → trigger retraining (force=false by default)
    GET  /api/v1/monitoring/health           → combined MLOps health snapshot
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["mlops monitoring"])

_DRIFT_REPORT_DIR = "logs/drift"
_REFERENCE_DATA = "data/raw/Crop_recommendation.csv"
_PREDICTION_LOG = "logs/prediction_log.jsonl"


# ── Request / Response models ────────────────────────────────────────────────

class DriftRunRequest(BaseModel):
    run_id: str | None = None
    prediction_log_path: str = _PREDICTION_LOG
    report_dir: str = _DRIFT_REPORT_DIR


class RetrainRequest(BaseModel):
    force: bool = False
    use_mlflow: bool = False


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_import_drift():
    try:
        from backend.ml.drift_monitor import (
            load_reference_data, load_prediction_log,
            run_drift_detection, get_latest_drift_summary, get_drift_history,
        )
        return load_reference_data, load_prediction_log, run_drift_detection, \
               get_latest_drift_summary, get_drift_history
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Drift monitor unavailable: {exc}",
        )


def _safe_import_trigger():
    try:
        from backend.ml.retrain_trigger import run_trigger, get_retrain_history
        return run_trigger, get_retrain_history
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Retrain trigger unavailable: {exc}",
        )


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/health", status_code=status.HTTP_200_OK)
def monitoring_health() -> dict[str, Any]:
    """Combined MLOps health snapshot — drift + retrain status at a glance."""
    (_, _, _, get_latest_drift_summary, _) = _safe_import_drift()
    (_, get_retrain_history) = _safe_import_trigger()

    drift = get_latest_drift_summary(_DRIFT_REPORT_DIR)
    retrain_history = get_retrain_history(last_n=1)
    last_retrain = retrain_history[-1] if retrain_history else None

    from backend.ml.prediction_logger import count_logged_predictions
    logged_count = count_logged_predictions(_PREDICTION_LOG)

    return {
        "mlops_status": "ok",
        "drift_monitoring": {
            "last_run": drift["timestamp"] if drift else None,
            "drift_detected": drift["drift_detected"] if drift else None,
            "drift_share_pct": round(drift["drift_share"] * 100, 1) if drift else None,
            "drifted_features": drift["drifted_feature_count"] if drift else None,
            "alert": drift["alert"] if drift else None,
        },
        "retraining": {
            "last_triggered": last_retrain["timestamp"] if last_retrain else None,
            "last_succeeded": last_retrain.get("retrain_succeeded") if last_retrain else None,
            "last_promoted": last_retrain.get("promoted") if last_retrain else None,
        },
        "prediction_log": {
            "logged_inputs": logged_count,
        },
    }


@router.get("/drift/latest", status_code=status.HTTP_200_OK)
def get_latest_drift() -> dict[str, Any]:
    """Return the most recent drift detection summary."""
    (_, _, _, get_latest_drift_summary, _) = _safe_import_drift()
    summary = get_latest_drift_summary(_DRIFT_REPORT_DIR)
    if summary is None:
        return {"message": "No drift runs yet. POST /monitoring/drift/run to start."}
    return summary


@router.get("/drift/history", status_code=status.HTTP_200_OK)
def get_drift_history_endpoint(
    last_n: int = Query(default=30, ge=1, le=200, description="Number of recent drift runs to return"),
) -> list[dict]:
    """Return time-series drift history for dashboards and charts."""
    (_, _, _, _, get_drift_history) = _safe_import_drift()
    return get_drift_history(_DRIFT_REPORT_DIR, last_n=last_n)


@router.get("/retrain/history", status_code=status.HTTP_200_OK)
def get_retrain_history_endpoint(
    last_n: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    """Return history of retraining events."""
    (_, get_retrain_history) = _safe_import_trigger()
    return get_retrain_history(last_n=last_n)


@router.post("/drift/run", status_code=status.HTTP_200_OK)
def run_drift_now(payload: DriftRunRequest) -> dict[str, Any]:
    """Run Evidently drift detection immediately and return the summary."""
    (load_reference_data, load_prediction_log,
     run_drift_detection, _, _) = _safe_import_drift()
    try:
        ref = load_reference_data(_REFERENCE_DATA)
        cur = load_prediction_log(payload.prediction_log_path)
        summary = run_drift_detection(
            ref, cur,
            report_dir=payload.report_dir,
            run_id=payload.run_id,
        )
        # Strip full feature_drift detail for API response (too large)
        return {k: v for k, v in summary.items() if k != "feature_drift"} | {
            "feature_drift_summary": {
                col: info["drift_detected"]
                for col, info in summary.get("feature_drift", {}).items()
            }
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Drift detection failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/retrain/trigger", status_code=status.HTTP_200_OK)
def trigger_retrain(payload: RetrainRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Trigger retraining in the background.
    Returns immediately with status=queued. Check /retrain/history for results.
    """
    (run_trigger, _) = _safe_import_trigger()

    def _bg():
        try:
            result = run_trigger(force=payload.force, use_mlflow=payload.use_mlflow)
            LOGGER.info("Background retrain complete: %s", result)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Background retrain failed: %s", exc)

    background_tasks.add_task(_bg)
    return {
        "status": "queued",
        "force": payload.force,
        "message": "Retraining queued in background. Poll GET /monitoring/retrain/history for results.",
    }
