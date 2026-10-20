"""
src/models/maize_disease/dataset.py
───────────────────────────────────
Dataset discovery, validation, stratified splitting, and tf.data input pipeline
for the maize leaf disease classification model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers

DEFAULT_DATA_DIR = Path("data/maize_leaf_disease")
IMAGE_SIZE = (224, 224)


def discover_and_summarize_dataset(data_dir: Path | str = DEFAULT_DATA_DIR) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Inspects the dataset directory, discovers all classes, counts images,
    validates readability, and generates a structured dataset summary.
    """
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Dataset directory not found at: {root}")

    # Discover classes from subdirectories
    classes = sorted([d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith(('.', '_', 'splits'))])
    if not classes:
        raise ValueError(f"No class subdirectories found in {root}")

    records = []
    modes = {}
    corrupted = []
    dimensions = {}

    for label_idx, class_name in enumerate(classes):
        class_dir = root / class_name
        for img_path in sorted(class_dir.iterdir()):
            if img_path.is_file() and img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                try:
                    with Image.open(img_path) as im:
                        im_mode = im.mode
                        im_size = im.size
                    modes[im_mode] = modes.get(im_mode, 0) + 1
                    dimensions[f"{im_size[0]}x{im_size[1]}"] = dimensions.get(f"{im_size[0]}x{im_size[1]}", 0) + 1
                    records.append({
                        "filepath": str(img_path.resolve()),
                        "filename": img_path.name,
                        "class_name": class_name,
                        "label_idx": label_idx,
                        "width": im_size[0],
                        "height": im_size[1],
                        "mode": im_mode,
                    })
                except Exception as err:
                    corrupted.append({"filepath": str(img_path), "error": str(err)})

    df = pd.DataFrame(records)
    total_images = len(df)
    class_distribution = df["class_name"].value_counts().to_dict()

    summary = {
        "dataset_root": str(root.resolve()),
        "total_images": total_images,
        "classes": classes,
        "num_classes": len(classes),
        "class_to_idx": {c: i for i, c in enumerate(classes)},
        "class_distribution": class_distribution,
        "class_proportions": {c: round(count / total_images, 4) for c, count in class_distribution.items()},
        "color_modes": modes,
        "corrupted_images_count": len(corrupted),
        "corrupted_images": corrupted,
    }

    return df, summary


def create_stratified_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
    save_dir: Path | str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Creates stratified splits (70% train, 15% validation, 15% test) preserving
    class proportions and guaranteeing zero leakage across subsets.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1.0"

    # Step 1: Split into train and temp (val + test)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        stratify=df["class_name"],
        random_state=random_seed,
    )

    # Step 2: Split temp equally into val and test (50% of temp = 15% of total)
    val_test_ratio = test_ratio / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=val_test_ratio,
        stratify=temp_df["class_name"],
        random_state=random_seed,
    )

    # Validate zero intersection
    train_paths = set(train_df["filepath"])
    val_paths = set(val_df["filepath"])
    test_paths = set(test_df["filepath"])

    assert len(train_paths.intersection(val_paths)) == 0, "Leakage detected between train and val!"
    assert len(train_paths.intersection(test_paths)) == 0, "Leakage detected between train and test!"
    assert len(val_paths.intersection(test_paths)) == 0, "Leakage detected between val and test!"

    if save_dir:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        train_df.to_csv(out_dir / "train.csv", index=False)
        val_df.to_csv(out_dir / "val.csv", index=False)
        test_df.to_csv(out_dir / "test.csv", index=False)

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


# Data Augmentation pipeline applied exclusively to training set
TRAIN_AUGMENTATION_LAYERS = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.08),  # +/- ~30 degrees
    layers.RandomZoom((-0.08, 0.08)),  # +/- 8% zoom
    layers.RandomTranslation(0.05, 0.05),  # +/- 5% shift
], name="maize_leaf_data_augmentation")


def _load_and_preprocess_image(filepath: tf.Tensor, target_size: tuple[int, int] = IMAGE_SIZE) -> tf.Tensor:
    """Reads image file from disk, converts to RGB, resizes, and scales for MobileNetV2."""
    raw = tf.io.read_file(filepath)
    # decode_image handles JPEG, PNG and ensures 3 color channels (RGB)
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    img = tf.image.resize(img, target_size)
    img.set_shape([target_size[0], target_size[1], 3])
    # MobileNetV2 preprocessing scales inputs to [-1, 1]
    img = tf.keras.applications.mobilenet_v2.preprocess_input(img)
    return img


def build_tf_dataset(
    df: pd.DataFrame,
    batch_size: int = 32,
    is_training: bool = False,
    num_classes: int = 4,
    target_size: tuple[int, int] = IMAGE_SIZE,
    shuffle_buffer: int = 1024,
    random_seed: int = 42,
) -> tf.data.Dataset:
    """
    Builds a high-performance tf.data pipeline with streaming decode,
    preprocessing, optional training augmentation, batching, and prefetching.
    """
    filepaths = df["filepath"].tolist()
    labels = df["label_idx"].tolist()

    # Convert labels to one-hot encoding for categorical crossentropy
    one_hot_labels = tf.one_hot(labels, depth=num_classes)

    ds = tf.data.Dataset.from_tensor_slices((filepaths, one_hot_labels))

    if is_training:
        ds = ds.shuffle(buffer_size=min(len(filepaths), shuffle_buffer), seed=random_seed, reshuffle_each_iteration=True)

    def _process_item(path, label):
        img = _load_and_preprocess_image(path, target_size=target_size)
        return img, label

    ds = ds.map(_process_item, num_parallel_calls=tf.data.AUTOTUNE)

    if is_training:
        ds = ds.map(lambda x, y: (TRAIN_AUGMENTATION_LAYERS(x, training=True), y), num_parallel_calls=tf.data.AUTOTUNE)

    ds = ds.batch(batch_size)
    ds = ds.prefetch(buffer_size=tf.data.AUTOTUNE)

    return ds
