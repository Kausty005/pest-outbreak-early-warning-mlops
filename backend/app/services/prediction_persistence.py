from __future__ import annotations

import logging

from ..db.database import DatabaseManager
from ..db.models import CropPrediction, FertilizerPrediction

LOGGER = logging.getLogger(__name__)


def persist_prediction(database: DatabaseManager, result: dict, farm_id: str | None) -> str:
    if not database.available:
        return "disabled" if not database.enabled else "unavailable"
    try:
        with database.session() as session:
            session.add(
                CropPrediction(
                    prediction_id=result["prediction_id"],
                    farm_id=farm_id,
                    inputs=result["input_summary"],
                    predicted_crop=result["predicted_crop"],
                    candidate_scores=result["top_recommendations"],
                    model_version=result["model_version"],
                )
            )
            session.commit()
        return "stored"
    except Exception:
        LOGGER.exception("Prediction persistence failed; returning inference result without persistence")
        return "unavailable"


def persist_fertilizer_prediction(database: DatabaseManager, result: dict, inputs: dict, farm_id: str | None) -> str:
    if not database.available:
        return "disabled" if not database.enabled else "unavailable"
    try:
        with database.session() as session:
            session.add(
                FertilizerPrediction(
                    prediction_id=result["prediction_id"],
                    farm_id=farm_id,
                    crop=result["crop"],
                    state_name=result["state_name"],
                    inputs=inputs,
                    recommendations=result["recommendations"],
                    commercial_equivalents=result["fertilizer_commercial_equivalent_approx"],
                    model_version=result["model_version"],
                )
            )
            session.commit()
        return "stored"
    except Exception:
        LOGGER.exception("Fertilizer prediction persistence failed; returning inference result without persistence")
        return "unavailable"
