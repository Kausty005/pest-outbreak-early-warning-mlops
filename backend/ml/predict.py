"""Artifact-backed prediction functions used by the API, never by reimplemented features."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from .data_validation import FEATURE_COLUMNS

DISCLAIMER = (
    "Model-based prediction from a limited historical dataset; it is not independently "
    "validated for farm-specific suitability or a guarantee of crop success."
)


def recommend(model, inputs: dict[str, float], model_version: str) -> dict[str, Any]:
    frame = pd.DataFrame([{column: inputs[column] for column in FEATURE_COLUMNS}])
    probabilities = np.asarray(model.predict_proba(frame)[0], dtype=float)
    classes = [str(label) for label in model.classes_]
    ranked = sorted(zip(classes, probabilities), key=lambda pair: pair[1], reverse=True)
    candidates = [
        {"crop": crop, "model_score": round(float(score), 6)}
        for crop, score in ranked[:3]
    ]
    return {
        "prediction_id": str(uuid4()),
        "predicted_crop": candidates[0]["crop"],
        "top_recommendations": candidates,
        "model_version": model_version,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": {column: float(inputs[column]) for column in FEATURE_COLUMNS},
        "confidence_note": "Model score is an uncalibrated class score, not a verified probability of crop success.",
        "disclaimer": DISCLAIMER,
    }
