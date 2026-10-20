"""
src/models/maize_disease/train.py
─────────────────────────────────
End-to-end training, fine-tuning, evaluation, and artifact serialization pipeline
for the MobileNetV2 Maize Leaf Disease Classification Model.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

from .dataset import (
    discover_and_summarize_dataset,
    create_stratified_splits,
    build_tf_dataset,
    IMAGE_SIZE,
)
from .model import (
    build_mobilenetv2_classifier,
    compile_for_initial_training,
    unfreeze_for_fine_tuning,
)

LOGGER = logging.getLogger("maize_disease_trainer")
RANDOM_SEED = 42


def set_reproducibility_seeds(seed: int = RANDOM_SEED) -> None:
    """Sets seeds for Python, NumPy, and TensorFlow for reproducible runs."""
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def plot_and_save_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    save_path: Path | str,
) -> None:
    """Plots and saves an annotated confusion matrix heatmap."""
    plt.figure(figsize=(7, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True,
    )
    plt.title("Maize Leaf Disease Confusion Matrix (Held-out Test Set)", fontsize=13, pad=12)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("Ground Truth Class", fontsize=11)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()


def plot_and_save_training_history(
    history_combined: dict[str, list[float]],
    save_path: Path | str,
) -> None:
    """Plots and saves combined training and validation loss and accuracy curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    epochs = range(1, len(history_combined["accuracy"]) + 1)

    # Accuracy plot
    ax1.plot(epochs, history_combined["accuracy"], "b-o", label="Training Accuracy", markersize=4)
    ax1.plot(epochs, history_combined["val_accuracy"], "g-s", label="Validation Accuracy", markersize=4)
    ax1.set_title("Training & Validation Accuracy", fontsize=12)
    ax1.set_xlabel("Epoch", fontsize=10)
    ax1.set_ylabel("Accuracy", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="lower right")

    # Loss plot
    ax2.plot(epochs, history_combined["loss"], "r-o", label="Training Loss", markersize=4)
    ax2.plot(epochs, history_combined["val_loss"], "m-s", label="Validation Loss", markersize=4)
    ax2.set_title("Training & Validation Loss", fontsize=12)
    ax2.set_xlabel("Epoch", fontsize=10)
    ax2.set_ylabel("Loss", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()


def run_training_pipeline(
    data_dir: str = "data/maize_leaf_disease",
    output_dir: str = "models/maize_disease",
    batch_size: int = 32,
    epochs_stage1: int = 6,
    epochs_stage2: int = 6,
    lr_stage1: float = 1e-3,
    lr_stage2: float = 1e-4,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """
    Executes complete training, fine-tuning, evaluation, and artifact saving pipeline.
    """
    set_reproducibility_seeds(random_seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("STEP 1: INSPECTING & PREPARING MAIZE LEAF DISEASE DATASET")
    print("=" * 75)

    df, summary = discover_and_summarize_dataset(data_dir)
    class_names = summary["classes"]
    num_classes = len(class_names)
    class_to_idx = summary["class_to_idx"]

    print(f"Dataset root:       {summary['dataset_root']}")
    print(f"Discovered classes: {class_names} ({num_classes} classes)")
    print(f"Total images:       {summary['total_images']}")
    print(f"Class counts:       {summary['class_distribution']}")
    print(f"Class proportions:  {summary['class_proportions']}")
    print(f"Corrupted images:   {summary['corrupted_images_count']}")

    # Step 2: Stratified Split 70% train / 15% val / 15% test
    splits_dir = Path(data_dir) / "splits"
    train_df, val_df, test_df = create_stratified_splits(
        df,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=random_seed,
        save_dir=splits_dir,
    )

    print("\n" + "=" * 75)
    print("STEP 2: STRATIFIED SPLITS CREATED (ZERO CROSS-SPLIT LEAKAGE)")
    print("=" * 75)
    print(f"Training split:   {len(train_df):>5} images ({len(train_df)/len(df):.1%})")
    print(f"Validation split: {len(val_df):>5} images ({len(val_df)/len(df):.1%})")
    print(f"Held-out test:    {len(test_df):>5} images ({len(test_df)/len(df):.1%})")

    # Build memory-efficient streaming tf.data pipelines
    train_ds = build_tf_dataset(train_df, batch_size=batch_size, is_training=True, num_classes=num_classes)
    val_ds = build_tf_dataset(val_df, batch_size=batch_size, is_training=False, num_classes=num_classes)
    test_ds = build_tf_dataset(test_df, batch_size=batch_size, is_training=False, num_classes=num_classes)

    # Step 3: Model construction
    print("\n" + "=" * 75)
    print("STEP 3: BUILDING MOBILENETV2 CNN CLASSIFIER")
    print("=" * 75)

    gpus = tf.config.list_physical_devices("GPU")
    hardware = "GPU" if gpus else "CPU (TensorFlow AVX2/oneDNN optimized)"
    print(f"Compute hardware detected: {hardware}")

    model, base_model = build_mobilenetv2_classifier(num_classes=num_classes, input_shape=(*IMAGE_SIZE, 3))
    compile_for_initial_training(model, learning_rate=lr_stage1)
    model.summary(print_fn=lambda x: None)  # verify cleanly constructed
    print(f"Total model parameters: {model.count_params():,}")
    print(f"Trainable parameters (head): {sum(p.numpy().size for p in model.trainable_variables):,}")

    # Callbacks
    best_model_file = out_path / "maize_disease_model.keras"
    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=str(best_model_file),
        monitor="val_loss",
        save_best_only=True,
        verbose=1,
    )
    early_stop_cb = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True,
        verbose=1,
    )
    reduce_lr_cb = tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=1e-6,
        verbose=1,
    )

    history_combined = {
        "accuracy": [],
        "val_accuracy": [],
        "loss": [],
        "val_loss": [],
        "lr": [],
    }

    # Stage 1: Feature Extraction (Backbone frozen)
    print("\n" + "-" * 75)
    print(f"STAGE 1 TRAINING: Training Classification Head ({epochs_stage1} epochs, lr={lr_stage1})")
    print("-" * 75)

    start_time = time.time()
    hist1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_stage1,
        callbacks=[checkpoint_cb, reduce_lr_cb],
        verbose=1,
    )

    for k in ["accuracy", "val_accuracy", "loss", "val_loss"]:
        history_combined[k].extend(hist1.history[k])

    # Stage 2: Fine-Tuning (Unfreeze top layers of MobileNetV2)
    print("\n" + "-" * 75)
    print(f"STAGE 2 FINE-TUNING: Unfreezing Top Layers from Layer 100 ({epochs_stage2} epochs, lr={lr_stage2})")
    print("-" * 75)

    unfreeze_for_fine_tuning(model, base_model, unfreeze_from_layer=100, learning_rate=lr_stage2)
    print(f"Trainable parameters in fine-tuning: {sum(p.numpy().size for p in model.trainable_variables):,}")

    hist2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_stage1 + epochs_stage2,
        initial_epoch=epochs_stage1,
        callbacks=[checkpoint_cb, early_stop_cb, reduce_lr_cb],
        verbose=1,
    )

    for k in ["accuracy", "val_accuracy", "loss", "val_loss"]:
        history_combined[k].extend(hist2.history[k])

    training_duration_seconds = round(time.time() - start_time, 2)
    print(f"\nTraining completed in {training_duration_seconds}s")

    # Reload best saved model
    print("\n" + "=" * 75)
    print("STEP 4: EVALUATING BEST SAVED MODEL ON HELD-OUT TEST SET")
    print("=" * 75)

    best_model = tf.keras.models.load_model(str(best_model_file))

    # Evaluate loss and accuracy
    test_eval = best_model.evaluate(test_ds, verbose=0)
    test_loss = float(test_eval[0])
    test_accuracy = float(test_eval[1])

    # Predict full test set
    y_true_indices = test_df["label_idx"].to_numpy()
    test_preds = best_model.predict(test_ds, verbose=0)
    y_pred_indices = np.argmax(test_preds, axis=-1)
    y_confidences = np.max(test_preds, axis=-1)

    # Classification report
    clf_report = classification_report(
        y_true_indices,
        y_pred_indices,
        target_names=class_names,
        output_dict=True,
    )
    clf_report_text = classification_report(
        y_true_indices,
        y_pred_indices,
        target_names=class_names,
    )

    # Confusion matrix
    cm = confusion_matrix(y_true_indices, y_pred_indices)

    print("\n[Held-Out Test Set Metrics]:")
    print(f"  • Test Loss:     {test_loss:.4f}")
    print(f"  • Test Accuracy: {test_accuracy:.4%}")
    print("\n[Detailed Classification Report]:\n" + clf_report_text)
    print("\n[Confusion Matrix]:\n", cm)

    # Sample correct & misclassified instances
    correct_samples = []
    incorrect_samples = []
    for idx, (true_idx, pred_idx, conf) in enumerate(zip(y_true_indices, y_pred_indices, y_confidences)):
        sample_info = {
            "image_filename": test_df.iloc[idx]["filename"],
            "image_filepath": test_df.iloc[idx]["filepath"],
            "ground_truth": class_names[true_idx],
            "predicted": class_names[pred_idx],
            "confidence": round(float(conf), 4),
        }
        if true_idx == pred_idx and len(correct_samples) < 5:
            correct_samples.append(sample_info)
        elif true_idx != pred_idx and len(incorrect_samples) < 5:
            incorrect_samples.append(sample_info)

    # Step 5: Save Artifacts & Metadata
    print("\n" + "=" * 75)
    print("STEP 5: SAVING ARTIFACTS AND METADATA")
    print("=" * 75)

    # 1. class_names.json
    class_metadata = {
        "classes": class_names,
        "class_to_idx": class_to_idx,
        "idx_to_class": {i: c for i, c in enumerate(class_names)},
        "num_classes": num_classes,
        "healthy_class": "healthy",
        "disease_classes": [c for c in class_names if c != "healthy"],
    }
    (out_path / "class_names.json").write_text(json.dumps(class_metadata, indent=2), encoding="utf-8")

    # 2. training_config.json
    config_metadata = {
        "model_name": "AgriAdapt-MaizeLeafDisease-MobileNetV2",
        "model_version": "1.0.0",
        "architecture": "MobileNetV2 (ImageNet) + GAP + Dropout(0.3) + Dense(4, softmax)",
        "input_shape": [*IMAGE_SIZE, 3],
        "batch_size": batch_size,
        "epochs_stage1": epochs_stage1,
        "epochs_stage2": epochs_stage2,
        "lr_stage1": lr_stage1,
        "lr_stage2": lr_stage2,
        "optimizer": "Adam",
        "loss": "categorical_crossentropy",
        "random_seed": random_seed,
        "hardware_platform": hardware,
        "training_duration_seconds": training_duration_seconds,
        "split_counts": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "total": len(df),
        },
        "data_augmentation_layers": [
            "RandomFlip(horizontal)",
            "RandomRotation(0.08)",
            "RandomZoom((-0.08, 0.08))",
            "RandomTranslation(0.05, 0.05)",
        ],
    }
    (out_path / "training_config.json").write_text(json.dumps(config_metadata, indent=2), encoding="utf-8")

    # 3. evaluation_report.json
    evaluation_metadata = {
        "test_loss": test_loss,
        "test_accuracy": test_accuracy,
        "macro_avg_f1": clf_report["macro avg"]["f1-score"],
        "weighted_avg_f1": clf_report["weighted avg"]["f1-score"],
        "per_class_metrics": {
            cls_name: {
                "precision": round(clf_report[cls_name]["precision"], 4),
                "recall": round(clf_report[cls_name]["recall"], 4),
                "f1_score": round(clf_report[cls_name]["f1-score"], 4),
                "support": int(clf_report[cls_name]["support"]),
            }
            for cls_name in class_names
        },
        "confusion_matrix": cm.tolist(),
        "sample_correctly_classified": correct_samples,
        "sample_misclassified": incorrect_samples,
    }
    (out_path / "evaluation_report.json").write_text(json.dumps(evaluation_metadata, indent=2), encoding="utf-8")

    # 4. Plots
    cm_path = out_path / "confusion_matrix.png"
    plot_and_save_confusion_matrix(cm, class_names, cm_path)

    history_path = out_path / "training_history.png"
    plot_and_save_training_history(history_combined, history_path)

    print(f"Artifacts saved in {out_path}:")
    print(f"  • Model:            {best_model_file.name} ({best_model_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"  • Class names:      class_names.json")
    print(f"  • Training config:  training_config.json")
    print(f"  • Evaluation:       evaluation_report.json")
    print(f"  • Confusion matrix: {cm_path.name}")
    print(f"  • History plot:     {history_path.name}")

    return {
        "summary": summary,
        "config": config_metadata,
        "evaluation": evaluation_metadata,
        "model_file": str(best_model_file),
    }


def main():
    parser = argparse.ArgumentParser(description="Train MobileNetV2 Maize Leaf Disease CNN")
    parser.add_argument("--data-dir", default="data/maize_leaf_disease", help="Path to maize leaf dataset directory")
    parser.add_argument("--output-dir", default="models/maize_disease", help="Path to output models directory")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training and evaluation")
    parser.add_argument("--epochs-stage1", type=int, default=6, help="Epochs for classification head training")
    parser.add_argument("--epochs-stage2", type=int, default=6, help="Epochs for fine-tuning top layers")
    parser.add_argument("--lr-stage1", type=float, default=1e-3, help="Learning rate for stage 1")
    parser.add_argument("--lr-stage2", type=float, default=1e-4, help="Learning rate for stage 2")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility")

    args = parser.parse_args()

    # Automatic batch-size reduction if memory is constrained
    batch_size = args.batch_size
    try:
        import psutil
        avail_gb = psutil.virtual_memory().available / (1024**3)
        if avail_gb < 2.0 and batch_size > 16:
            print(f"Notice: Available RAM is {avail_gb:.2f} GB. Automatically setting batch_size to 16 for safety.")
            batch_size = 16
    except Exception:
        pass

    run_training_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=batch_size,
        epochs_stage1=args.epochs_stage1,
        epochs_stage2=args.epochs_stage2,
        lr_stage1=args.lr_stage1,
        lr_stage2=args.lr_stage2,
        random_seed=args.seed,
    )


if __name__ == "__main__":
    main()
