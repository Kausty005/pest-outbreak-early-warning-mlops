from __future__ import annotations

import json
import logging
from typing import Any

import joblib

from ...ml.predict import recommend
from ..core.config import Settings

LOGGER = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    pass


class CropModelService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model: Any | None = None
        self.metadata: dict[str, Any] | None = None
        self.load_error: str | None = None

    @property
    def available(self) -> bool:
        return self.model is not None and self.metadata is not None

    @property
    def model_version(self) -> str | None:
        return self.metadata.get("model_version") if self.metadata else None

    def load(self) -> None:
        self.model = None
        self.metadata = None
        self.load_error = None
        if not self.settings.model_path.exists() or not self.settings.metadata_path.exists():
            self.load_error = "Model artifact is not present. Run the documented training command first."
            LOGGER.warning(self.load_error)
            return
        try:
            self.model = joblib.load(self.settings.model_path)
            self.metadata = json.loads(self.settings.metadata_path.read_text(encoding="utf-8"))
            if not self.metadata.get("model_version"):
                raise ValueError("metadata.json does not contain model_version")
            LOGGER.info("Loaded crop model version %s", self.model_version)
        except Exception:
            self.model = None
            self.metadata = None
            self.load_error = "Model artifact could not be loaded. Retrain or restore a valid artifact."
            LOGGER.exception("Model loading failed")

    def prediction(self, inputs: dict[str, float]) -> dict[str, Any]:
        if not self.available:
            raise ModelUnavailableError(self.load_error or "No model is loaded")
        return recommend(self.model, inputs, self.model_version or "unknown")

    def model_info(self) -> dict[str, Any]:
        if not self.available:
            return {
                "model_available": False,
                "model_version": None,
                "selected_model": None,
                "evaluation_metrics": None,
                "dataset_checksum": None,
                "disclaimer": self.load_error or "No model is loaded.",
            }
        dataset = self.metadata.get("dataset", {})
        return {
            "model_available": True,
            "model_version": self.model_version,
            "selected_model": self.metadata.get("selected_model"),
            "evaluation_metrics": self.metadata.get("evaluation_metrics"),
            "dataset_checksum": dataset.get("checksum_sha256"),
            "disclaimer": "Evaluation reflects only the supplied dataset split; it is not external agronomic validation.",
        }
