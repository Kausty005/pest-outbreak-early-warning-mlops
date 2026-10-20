"""Evaluation helpers kept separate from model fitting."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


def classification_metrics(y_true, y_pred, labels: list[str]) -> dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": classification_report(
            y_true,
            y_pred,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "labels": labels,
    }


def feature_importance(pipeline) -> list[dict[str, float | str]]:
    """Return native tree importances when the selected estimator exposes them."""
    estimator = pipeline.named_steps["model"]
    importances = getattr(estimator, "feature_importances_", None)
    if importances is None:
        return []
    preprocessor = pipeline.named_steps["preprocess"]
    names = list(preprocessor.get_feature_names_out())
    pairs = [
        {"feature": str(name), "importance": float(importance)}
        for name, importance in zip(names, np.asarray(importances), strict=True)
    ]
    return sorted(pairs, key=lambda item: item["importance"], reverse=True)
