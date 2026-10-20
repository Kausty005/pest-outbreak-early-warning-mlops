"""Evaluation metrics, threshold tuning, and visualization for pest outbreak forecasting."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class EvaluationMetrics:
    split_name: str
    model_name: str
    threshold: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    true_negatives: int
    false_positives: int  # Unnecessary simulated alerts
    false_negatives: int  # Missed simulated outbreaks
    true_positives: int
    total_samples: int
    positive_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_predictions(
    y_true: np.ndarray | Sequence[int],
    y_pred: np.ndarray | Sequence[int],
    y_prob: np.ndarray | Sequence[float] | None = None,
    model_name: str = "Model",
    split_name: str = "validation",
    threshold: float = 0.50,
) -> EvaluationMetrics:
    """
    Calculate comprehensive binary classification metrics tailored for imbalanced
    pest outbreak forecasting.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_pred_arr = np.asarray(y_pred, dtype=int)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    # ROC-AUC and PR-AUC calculation
    if y_prob is not None:
        y_prob_arr = np.asarray(y_prob, dtype=float)
        try:
            roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
        except Exception:
            roc_auc = 0.5
        try:
            pr_auc = float(average_precision_score(y_true_arr, y_prob_arr))
        except Exception:
            pr_auc = float(y_true_arr.mean())
    else:
        roc_auc = 0.5
        pr_auc = float(y_true_arr.mean())

    return EvaluationMetrics(
        split_name=split_name,
        model_name=model_name,
        threshold=round(float(threshold), 3),
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1=round(f1, 4),
        roc_auc=round(roc_auc, 4),
        pr_auc=round(pr_auc, 4),
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        true_positives=tp,
        total_samples=len(y_true_arr),
        positive_rate=round(float(y_true_arr.mean()), 4),
    )


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "f1",
) -> tuple[float, float]:
    """
    Search thresholds from 0.05 to 0.95 to find the threshold that optimizes
    the specified metric on validation probabilities.

    CRITICAL: This function must ONLY be run on validation data, NEVER on test data.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    thresholds = np.linspace(0.05, 0.95, 91)
    best_thresh = 0.50
    best_score = -1.0

    for t in thresholds:
        preds = (y_prob_arr >= t).astype(int)
        if metric == "f1":
            score = f1_score(y_true_arr, preds, zero_division=0)
        elif metric == "recall":
            score = recall_score(y_true_arr, preds, zero_division=0)
        elif metric == "precision":
            score = precision_score(y_true_arr, preds, zero_division=0)
        else:
            score = f1_score(y_true_arr, preds, zero_division=0)

        if score > best_score:
            best_score = float(score)
            best_thresh = float(t)

    return round(best_thresh, 3), round(best_score, 4)


def plot_confusion_matrix(
    cm: np.ndarray,
    model_name: str,
    split_name: str,
    output_path: str | Path,
) -> None:
    """Plot and save a styled confusion matrix with agricultural alert annotations."""
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    classes = ["No Outbreak (0)", "Outbreak (1)"]
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=classes,
        yticklabels=classes,
        ylabel="Actual Simulated Ground Truth",
        xlabel="Predicted Warning",
        title=f"{model_name} Confusion Matrix\n({split_name.title()} Split)",
    )

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            label = f"{val:,}"
            if i == 0 and j == 1:
                label += "\n(False Alarm)"
            elif i == 1 and j == 0:
                label += "\n(Missed Outbreak)"
            elif i == 1 and j == 1:
                label += "\n(True Warning)"
            elif i == 0 and j == 0:
                label += "\n(True Negative)"

            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                color="white" if val > thresh else "black",
                fontsize=9,
            )

    fig.tight_layout()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
