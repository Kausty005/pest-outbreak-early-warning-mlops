"""
src/models/maize_disease/predict.py
───────────────────────────────────
Production inference engine for Maize Leaf Disease classification.
Applies exact training preprocessing and handles invalid inputs gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tensorflow as tf

DEFAULT_MODEL_DIR = Path("models/maize_disease")
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "maize_disease_model.keras"
DEFAULT_CLASS_NAMES_PATH = DEFAULT_MODEL_DIR / "class_names.json"
IMAGE_SIZE = (224, 224)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

DISCLAIMER = (
    "Confidence score is an uncalibrated classifier score based on visual leaf symptoms; "
    "it is not a guaranteed probability of disease presence or field severity. "
    "Consult an agricultural extension officer or plant pathologist for field diagnosis."
)


class MaizeDiseasePredictor:
    """Production predictor for maize leaf disease image classification."""

    def __init__(
        self,
        model_path: Path | str = DEFAULT_MODEL_PATH,
        class_names_path: Path | str = DEFAULT_CLASS_NAMES_PATH,
    ) -> None:
        self.model_path = Path(model_path)
        self.class_names_path = Path(class_names_path)
        self.model: tf.keras.Model | None = None
        self.class_names: list[str] = []
        self.class_to_idx: dict[str, int] = {}
        self.idx_to_class: dict[int, str] = {}
        self._load_resources()

    def _load_resources(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                "Train the model first using: python train_maize_disease.py"
            )
        if not self.class_names_path.exists():
            raise FileNotFoundError(
                f"Class metadata not found at {self.class_names_path}."
            )

        with open(self.class_names_path, encoding="utf-8") as f:
            metadata = json.load(f)
            self.class_names = metadata["classes"]
            self.class_to_idx = metadata.get("class_to_idx", {c: i for i, c in enumerate(self.class_names)})
            self.idx_to_class = {int(k) if isinstance(k, (int, str)) and str(k).isdigit() else self.class_to_idx[k]: v
                                for k, v in metadata.get("idx_to_class", {i: c for i, c in enumerate(self.class_names)}).items()}

        self.model = tf.keras.models.load_model(str(self.model_path))

    @staticmethod
    def preprocess_image(image_path: Path | str) -> np.ndarray:
        """
        Loads an image, validates format, converts to RGB, resizes to (224, 224),
        and applies MobileNetV2 normalization.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file does not exist: {path}")

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image extension '{path.suffix}'. "
                f"Supported formats are: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        try:
            with Image.open(path) as img:
                # Ensure 3-channel RGB (handles RGBA, grayscale, CMYK)
                img = img.convert("RGB")
                img = img.resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
                arr = np.array(img, dtype=np.float32)
        except Exception as e:
            raise ValueError(f"Corrupted or unreadable image file at {path}: {e}") from e

        # MobileNetV2 preprocessing: scales pixel values to [-1.0, 1.0]
        processed = tf.keras.applications.mobilenet_v2.preprocess_input(arr)
        # Expand batch dimension: (1, 224, 224, 3)
        return np.expand_dims(processed, axis=0)

    def predict(self, image_path: Path | str) -> dict[str, Any]:
        """
        Executes prediction on input image.

        Returns:
            Dictionary containing predicted class, confidence, all class scores, and disclaimer.
        """
        batch = self.preprocess_image(image_path)
        raw_probs = self.model.predict(batch, verbose=0)[0]

        pred_idx = int(np.argmax(raw_probs))
        predicted_class = self.class_names[pred_idx]
        confidence = float(raw_probs[pred_idx])

        all_scores = [
            {"class": cls_name, "score": round(float(raw_probs[i]), 5)}
            for i, cls_name in enumerate(self.class_names)
        ]
        all_scores = sorted(all_scores, key=lambda x: x["score"], reverse=True)

        is_healthy = predicted_class == "healthy"
        status_label = "HEALTHY" if is_healthy else "DISEASE_DETECTED"

        return {
            "image_path": str(Path(image_path).resolve()),
            "predicted_class": predicted_class,
            "status": status_label,
            "confidence": round(confidence, 4),
            "class_probabilities": all_scores,
            "model_version": "1.0.0",
            "disclaimer": DISCLAIMER,
        }
