"""Preprocessing pipeline definition for multi-crop pest outbreak forecasting."""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .dataset import (
    CATEGORICAL_COLUMNS,
    NUMERICAL_CONTINUOUS_COLUMNS,
    NUMERICAL_DISCRETE_COLUMNS,
)


def build_preprocessor(feature_columns: Sequence[str] | None = None) -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
    1. One-hot encodes categorical columns (district, crop, pest, growth_stage)
       with handle_unknown='ignore' so unseen categories at test time don't fail.
    2. Standardizes continuous numerical features (zero mean, unit variance).
    3. Passes through discrete / binary indicators (t7_high_rh_days, pest_present_t0).

    If feature_columns is provided, only the subset of features present in the list
    will be included in the respective transformers.

    IMPORTANT: This transformer MUST be fit strictly on training data only.
    """
    if feature_columns is None:
        cat_cols = CATEGORICAL_COLUMNS
        num_cont_cols = NUMERICAL_CONTINUOUS_COLUMNS
        num_disc_cols = NUMERICAL_DISCRETE_COLUMNS
    else:
        cat_cols = [c for c in CATEGORICAL_COLUMNS if c in feature_columns]
        num_cont_cols = [c for c in NUMERICAL_CONTINUOUS_COLUMNS if c in feature_columns]
        num_disc_cols = [c for c in NUMERICAL_DISCRETE_COLUMNS if c in feature_columns]

    transformers = []
    if cat_cols:
        categorical_transformer = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
        transformers.append(("cat", categorical_transformer, cat_cols))

    if num_cont_cols:
        continuous_transformer = StandardScaler()
        transformers.append(("num_cont", continuous_transformer, num_cont_cols))

    if num_disc_cols:
        transformers.append(("num_disc", "passthrough", num_disc_cols))

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return preprocessor


def build_model_pipeline(classifier, feature_columns: Sequence[str] | None = None) -> Pipeline:
    """
    Combine the feature preprocessor and an estimator into a single unified Pipeline.
    This guarantees that during both training and inference:
    - Preprocessing is fitted strictly on training data during pipeline.fit().
    - Transformations at inference time mirror training transformations identically.
    """
    preprocessor = build_preprocessor(feature_columns=feature_columns)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
    return pipeline

