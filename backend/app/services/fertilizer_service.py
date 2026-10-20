from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ...ml.fertilizer import FertilizerPredictor, get_example_input, VALID_CROPS
from ..core.config import Settings
from .model_service import ModelUnavailableError

LOGGER = logging.getLogger(__name__)


class FertilizerModelService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.predictor: FertilizerPredictor | None = None
        self.metadata: dict[str, Any] | None = None
        self.schema_data: dict[str, Any] | None = None
        self.load_error: str | None = None

    @property
    def available(self) -> bool:
        return self.predictor is not None and self.metadata is not None

    @property
    def model_version(self) -> str | None:
        return self.metadata.get("model_version") if self.metadata else None

    def load(self) -> None:
        self.predictor = None
        self.metadata = None
        self.schema_data = None
        self.load_error = None

        model_path = self.settings.fertilizer_model_path
        metadata_path = self.settings.fertilizer_metadata_path
        schema_path = self.settings.fertilizer_schema_path

        if not model_path.exists() or not metadata_path.exists():
            self.load_error = f"Fertilizer model artifact not found at {model_path}. Train or download the model artifact first."
            LOGGER.warning(self.load_error)
            return

        try:
            self.predictor = FertilizerPredictor(model_path=model_path)
            self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if schema_path.exists():
                self.schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
            LOGGER.info("Loaded fertilizer model version %s from %s", self.model_version, model_path)
        except Exception as exc:
            self.predictor = None
            self.metadata = None
            self.load_error = f"Fertilizer model artifact could not be loaded: {exc}"
            LOGGER.exception("Fertilizer model loading failed")

    def prediction(self, inputs: dict[str, Any]) -> dict[str, Any]:
        if not self.available or self.predictor is None:
            raise ModelUnavailableError(self.load_error or "No fertilizer model is loaded")

        raw_result = self.predictor.predict(inputs, return_format="dict")
        if isinstance(raw_result, list):
            raw_result = raw_result[0]

        return {
            "prediction_id": str(uuid4()),
            "crop": raw_result["crop"],
            "state_name": raw_result["state_name"],
            "recommendations": raw_result["recommendations"],
            "fertilizer_commercial_equivalent_approx": raw_result["fertilizer_commercial_equivalent_approx"],
            "model_version": self.model_version or "1.1.0",
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": raw_result.get(
                "disclaimer",
                "Baseline general recommendation for district agroclimatic zone. Adjust +/- 25% based on field-specific soil test rating and organic manure.",
            ),
        }

    def model_info(self) -> dict[str, Any]:
        if not self.available or self.metadata is None:
            return {
                "model_available": False,
                "model_version": None,
                "model_name": None,
                "model_type": None,
                "crops_covered": sorted(list(VALID_CROPS)),
                "framework": None,
                "validation_ensemble_weights": None,
                "disclaimer": self.load_error or "Fertilizer model is not loaded.",
            }

        return {
            "model_available": True,
            "model_version": self.model_version,
            "model_name": self.metadata.get("model_name"),
            "model_type": self.metadata.get("model_type"),
            "crops_covered": self.metadata.get("training_dataset", {}).get("crops_covered", sorted(list(VALID_CROPS))),
            "framework": self.metadata.get("framework"),
            "validation_ensemble_weights": self.metadata.get("validation_ensemble_weights"),
            "disclaimer": (
                "District agroclimatic baseline recommendation based on ICAR-IISS and Indian Soil Health Card data. "
                "Requires field-level STCR modulation based on farmer soil tests."
            ),
        }

    def schema(self) -> dict[str, Any]:
        if self.schema_data is not None:
            return self.schema_data
        return {
            "valid_crops": sorted(list(VALID_CROPS)),
            "nutrient_index_bounds": {"min": 0.8, "max": 3.2, "standard_range": [1.0, 3.0]},
            "percentage_bounds": {"min": 0.0, "max": 100.0},
            "required_fields": [
                "crop",
                "state_name",
                "nitrogen__nutrient_index",
                "phosphorus__nutrient_index",
                "potassium__nutrient_index",
                "soil_ph__nutrient_index",
                "organic_carbon__nutrient_index",
            ],
        }

    def example(self) -> dict[str, Any]:
        return get_example_input()
