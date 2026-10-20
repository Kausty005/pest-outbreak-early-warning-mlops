"""
src/models/maize_outbreak_forecasting/cnn_bridge.py
───────────────────────────────────────────────────
Clean integration bridge connecting the current-leaf CNN classifier
to the 7-day disease outbreak forecasting pipeline.

SCIENTIFIC PRINCIPLE:
The MobileNetV2 CNN diagnoses CURRENT visible symptoms on a photographed leaf at time t0.
It does NOT predict the future epidemic trajectory. This bridge extracts contemporaneous
symptom probabilities as optional observational covariates for the forecasting model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np

from ..maize_disease.predict import MaizeDiseasePredictor, DEFAULT_MODEL_PATH, DEFAULT_CLASS_NAMES_PATH


class CNNDiagnosticBridge:
    """
    Safely bridges the existing MobileNetV2 CNN classifier into the forecasting pipeline.
    Maintains strict architectural separation and enforces scientific disclaimer.
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
        class_names_path: str | Path = DEFAULT_CLASS_NAMES_PATH,
    ) -> None:
        self.model_path = Path(model_path)
        self.class_names_path = Path(class_names_path)
        self._predictor: MaizeDiseasePredictor | None = None

    @property
    def predictor(self) -> MaizeDiseasePredictor:
        if self._predictor is None:
            self._predictor = MaizeDiseasePredictor(
                model_path=self.model_path,
                class_names_path=self.class_names_path,
            )
        return self._predictor

    def extract_contemporaneous_symptom_feature(
        self,
        leaf_image_path: str | Path,
    ) -> dict[str, Any]:
        """
        Diagnose a leaf sampled at t0 to provide an observational symptom prior.

        Returns a dictionary containing:
          - leaf_image_filename
          - diagnosed_class_at_t0
          - common_rust_visual_probability (P(rust | leaf_t0))
          - all_class_probabilities
          - scientific_role: explicit explanation that this is a t0 covariate, NOT a future forecast.
        """
        img_p = Path(leaf_image_path)
        if not img_p.exists():
            raise FileNotFoundError(f"Leaf image not found: {img_p}")

        result = self.predictor.predict(img_p)

        # Extract common_rust probability
        prob_dict = {
            item["class"]: item["score"]
            for item in result["class_probabilities"]
        }
        rust_prob = prob_dict.get("common_rust", 0.0)

        return {
            "image_path": str(img_p),
            "diagnosed_class_at_t0": result["predicted_class"],
            "diagnosed_status_at_t0": result["status"],
            "common_rust_visual_probability_t0": float(rust_prob),
            "all_class_probabilities_t0": prob_dict,
            "feature_role": "Contemporaneous visual symptom covariate at observation date t0",
            "scientific_disclaimer": (
                "This visual score reflects current symptom presence on the sampled leaf at t0. "
                "It MUST NOT be interpreted as a 7-day future outbreak probability."
            ),
        }
