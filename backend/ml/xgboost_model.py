"""XGBoost adapter that preserves human-readable class labels at the pipeline boundary."""
from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.preprocessing import LabelEncoder


class LabelEncodedClassifier(ClassifierMixin, BaseEstimator):
    """Adapt estimators that require contiguous integer targets (notably XGBoost >= 3)."""

    def __init__(self, estimator) -> None:
        self.estimator = estimator

    def fit(self, X, y):
        self.label_encoder_ = LabelEncoder().fit(y)
        self.estimator_ = clone(self.estimator)
        self.estimator_.fit(X, self.label_encoder_.transform(y))
        self.classes_ = self.label_encoder_.classes_
        return self

    def predict(self, X):
        encoded = self.estimator_.predict(X)
        return self.label_encoder_.inverse_transform(np.asarray(encoded, dtype=int))

    def predict_proba(self, X):
        return self.estimator_.predict_proba(X)

    @property
    def feature_importances_(self):
        return self.estimator_.feature_importances_
