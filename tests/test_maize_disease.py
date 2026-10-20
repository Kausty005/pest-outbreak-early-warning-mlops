"""
tests/test_maize_disease.py
───────────────────────────
Unit and integration tests for the Maize Leaf Disease Classification model,
dataset pipeline, preprocessing, inference engine, and error handling.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from src.models.maize_disease.dataset import (
    discover_and_summarize_dataset,
    create_stratified_splits,
    _load_and_preprocess_image,
    IMAGE_SIZE,
)
from src.models.maize_disease.predict import (
    MaizeDiseasePredictor,
    SUPPORTED_EXTENSIONS,
    DEFAULT_MODEL_PATH,
    DEFAULT_CLASS_NAMES_PATH,
)


@pytest.fixture
def sample_test_image(tmp_path: Path) -> Path:
    """Creates a temporary synthetic RGB test image."""
    img_path = tmp_path / "synthetic_leaf.jpg"
    img = Image.new("RGB", (300, 300), color=(34, 139, 34))  # Forest green
    img.save(img_path, format="JPEG")
    return img_path


def test_dataset_discovery_and_class_integrity():
    data_dir = Path("data/maize_leaf_disease")
    if not data_dir.exists():
        pytest.skip("Dataset directory data/maize_leaf_disease not found.")

    df, summary = discover_and_summarize_dataset(data_dir)
    assert summary["total_images"] > 0
    assert summary["num_classes"] == 4
    assert set(summary["classes"]) == {"blight", "common_rust", "gray_leaf_spot", "healthy"}
    assert summary["corrupted_images_count"] == 0


def test_stratified_splitting_leakage_free():
    data_dir = Path("data/maize_leaf_disease")
    if not data_dir.exists():
        pytest.skip("Dataset directory not found.")

    df, _ = discover_and_summarize_dataset(data_dir)
    train_df, val_df, test_df = create_stratified_splits(
        df,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=42,
    )

    total = len(df)
    assert abs(len(train_df) / total - 0.70) < 0.01
    assert abs(len(val_df) / total - 0.15) < 0.01
    assert abs(len(test_df) / total - 0.15) < 0.01

    # Verify zero leakage across splits
    train_paths = set(train_df["filepath"])
    val_paths = set(val_df["filepath"])
    test_paths = set(test_df["filepath"])

    assert len(train_paths.intersection(val_paths)) == 0
    assert len(train_paths.intersection(test_paths)) == 0
    assert len(val_paths.intersection(test_paths)) == 0


def test_image_preprocessing_pipeline(sample_test_image: Path):
    tensor = _load_and_preprocess_image(str(sample_test_image), target_size=IMAGE_SIZE)
    assert tensor.shape == (224, 224, 3)

    # MobileNetV2 normalizes pixel values to [-1.0, 1.0]
    tensor_np = tensor.numpy()
    assert tensor_np.min() >= -1.05
    assert tensor_np.max() <= 1.05


def test_predictor_preprocessing_validation(sample_test_image: Path):
    batch = MaizeDiseasePredictor.preprocess_image(sample_test_image)
    assert batch.shape == (1, 224, 224, 3)
    assert batch.dtype == np.float32


def test_predictor_rejection_of_missing_file():
    with pytest.raises(FileNotFoundError, match="Image file does not exist"):
        MaizeDiseasePredictor.preprocess_image("non_existent_image_12345.jpg")


def test_predictor_rejection_of_unsupported_format(tmp_path: Path):
    invalid_file = tmp_path / "document.pdf"
    invalid_file.write_text("dummy content")

    with pytest.raises(ValueError, match="Unsupported image extension"):
        MaizeDiseasePredictor.preprocess_image(invalid_file)


def test_trained_model_inference_if_artifacts_present():
    if not DEFAULT_MODEL_PATH.exists() or not DEFAULT_CLASS_NAMES_PATH.exists():
        pytest.skip("Trained maize disease model artifact not yet available.")

    predictor = MaizeDiseasePredictor(
        model_path=DEFAULT_MODEL_PATH,
        class_names_path=DEFAULT_CLASS_NAMES_PATH,
    )
    assert len(predictor.class_names) == 4

    # Test inference on a real leaf from the dataset if available
    sample_img = None
    data_dir = Path("data/maize_leaf_disease")
    if data_dir.exists():
        for f in data_dir.glob("*/*.jpg"):
            sample_img = f
            break

    if sample_img:
        result = predictor.predict(sample_img)
        assert result["predicted_class"] in predictor.class_names
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["class_probabilities"]) == 4
        assert "disclaimer" in result
