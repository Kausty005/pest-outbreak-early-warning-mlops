"""
src/pest_forecasting/evaluate.py
────────────────────────────────
Evaluation metrics, threshold tuning, probability calibration,
and per-crop / per-pest evaluation for pest outbreak forecasting.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class EvaluationMetrics:
    model_name: str
    feature_set: str
    split_name: str
    threshold: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int
    total_samples: int
    positive_rate: float
    calibration_data: dict[str, list[float]]
    false_discovery_rate: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_calibration_assessment(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict[str, Any]:
    """
    Compute calibration curve and Expected Calibration Error (ECE).
    """
    try:
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
        # Compute ECE
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_assignments = np.digitize(y_prob, bin_edges) - 1
        bin_assignments = np.clip(bin_assignments, 0, n_bins - 1)
        
        ece = 0.0
        n_total = len(y_true)
        for b in range(n_bins):
            mask = bin_assignments == b
            if np.sum(mask) > 0:
                bin_acc = np.mean(y_true[mask])
                bin_conf = np.mean(y_prob[mask])
                ece += (np.sum(mask) / n_total) * abs(bin_acc - bin_conf)
                
        return {
            "prob_true": [round(float(v), 4) for v in prob_true],
            "prob_pred": [round(float(v), 4) for v in prob_pred],
            "expected_calibration_error": round(float(ece), 4),
        }
    except Exception:
        return {
            "prob_true": [],
            "prob_pred": [],
            "expected_calibration_error": 0.0,
        }


def evaluate_predictions(
    y_true: np.ndarray | Sequence[int],
    y_prob: np.ndarray | Sequence[float],
    model_name: str = "Model",
    feature_set: str = "FULL",
    split_name: str = "test",
    threshold: float = 0.50,
) -> EvaluationMetrics:
    """
    Calculate comprehensive metrics tailored for imbalanced pest outbreak forecasting.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)
    y_pred_arr = (y_prob_arr >= threshold).astype(int)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    try:
        roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
    except Exception:
        roc_auc = 0.5
    try:
        pr_auc = float(average_precision_score(y_true_arr, y_prob_arr))
    except Exception:
        pr_auc = float(y_true_arr.mean())

    try:
        brier = float(brier_score_loss(y_true_arr, y_prob_arr))
    except Exception:
        brier = 0.0

    calib = calculate_calibration_assessment(y_true_arr, y_prob_arr)

    fdr = float(fp / (tp + fp)) if (tp + fp) > 0 else 0.0
    fpr = float(fp / (tn + fp)) if (tn + fp) > 0 else 0.0
    fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0

    return EvaluationMetrics(
        model_name=model_name,
        feature_set=feature_set,
        split_name=split_name,
        threshold=round(float(threshold), 3),
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1=round(f1, 4),
        roc_auc=round(roc_auc, 4),
        pr_auc=round(pr_auc, 4),
        brier_score=round(brier, 4),
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        true_positives=tp,
        total_samples=len(y_true_arr),
        positive_rate=round(float(y_true_arr.mean()), 4),
        calibration_data=calib,
        false_discovery_rate=round(fdr, 4),
        false_positive_rate=round(fpr, 4),
        false_negative_rate=round(fnr, 4),
    )


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "f1",
) -> tuple[float, float]:
    """
    Search thresholds from 0.05 to 0.95 to find the threshold optimizing F1 or PR
    on VALIDATION data only.
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


def evaluate_slices_by_column(
    df_features: pd.DataFrame,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    column: str,
    threshold: float = 0.50,
) -> dict[str, dict[str, Any]]:
    """
    Compute sliced evaluation metrics across distinct categorical groups (e.g. crop or pest).
    """
    slices = {}
    unique_vals = sorted(df_features[column].unique().tolist())
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)
    y_pred_arr = (y_prob_arr >= threshold).astype(int)

    for val in unique_vals:
        idx = (df_features[column] == val).values
        if np.sum(idx) == 0:
            continue
        sub_true = y_true_arr[idx]
        sub_prob = y_prob_arr[idx]
        sub_pred = y_pred_arr[idx]

        sub_pr_auc = float(average_precision_score(sub_true, sub_prob)) if len(np.unique(sub_true)) > 1 else float(sub_true.mean())
        sub_roc_auc = float(roc_auc_score(sub_true, sub_prob)) if len(np.unique(sub_true)) > 1 else 0.5
        sub_f1 = float(f1_score(sub_true, sub_pred, zero_division=0))
        sub_prec = float(precision_score(sub_true, sub_pred, zero_division=0))
        sub_rec = float(recall_score(sub_true, sub_pred, zero_division=0))
        sub_brier = float(brier_score_loss(sub_true, sub_prob))

        slices[str(val)] = {
            "samples": int(np.sum(idx)),
            "outbreaks": int(np.sum(sub_true)),
            "prevalence_pct": round(float(np.mean(sub_true) * 100), 2),
            "pr_auc": round(sub_pr_auc, 4),
            "roc_auc": round(sub_roc_auc, 4),
            "f1": round(sub_f1, 4),
            "precision": round(sub_prec, 4),
            "recall": round(sub_rec, 4),
            "brier_score": round(sub_brier, 4),
        }
    return slices

