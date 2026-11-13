"""
src/pest_forecasting/preprocessor.py
────────────────────────────────────
Preprocessing pipeline definition for multi-crop pest outbreak forecasting.
Fitted strictly on training data partitions, avoiding any test leakage.
"""
from __future__ import annotations

from typing import Sequence
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .dataset import (
    CATEGORICAL_COLUMNS,
    ENVIRONMENTAL_NUMERICAL_CONTINUOUS,
    SCOUTING_NUMERICAL_CONTINUOUS,
    ENVIRONMENTAL_NUMERICAL_DISCRETE,
    SCOUTING_NUMERICAL_DISCRETE,
)


def build_preprocessor(feature_columns: Sequence[str] | None = None) -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
    1. Handles missing values defensively via SimpleImputer.
    2. One-hot encodes categorical columns (district, crop, pest, growth_stage)
       with handle_unknown='ignore' so unseen categories at test time don't fail.
    3. Standardizes continuous numerical features (zero mean, unit variance).
    4. Passes through discrete / binary indicators (t7_high_rh_days, pest_present_t0).

    Fitted strictly on training data only.
    """
    all_continuous = ENVIRONMENTAL_NUMERICAL_CONTINUOUS + SCOUTING_NUMERICAL_CONTINUOUS
    all_discrete = ENVIRONMENTAL_NUMERICAL_DISCRETE + SCOUTING_NUMERICAL_DISCRETE

    if feature_columns is None:
        cat_cols = list(CATEGORICAL_COLUMNS)
        num_cont_cols = list(all_continuous)
        num_disc_cols = list(all_discrete)
    else:
        cat_cols = [c for c in CATEGORICAL_COLUMNS if c in feature_columns]
        num_cont_cols = [c for c in all_continuous if c in feature_columns]
        num_disc_cols = [c for c in all_discrete if c in feature_columns]

    transformers = []

    if cat_cols:
        cat_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        transformers.append(("cat", cat_pipeline, cat_cols))

    if num_cont_cols:
        num_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("num_cont", num_pipeline, num_cont_cols))

    if num_disc_cols:
        disc_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("passthrough", "passthrough"),
            ]
        )
        transformers.append(("num_disc", disc_pipeline, num_disc_cols))

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return preprocessor


def build_model_pipeline(classifier, feature_columns: Sequence[str] | None = None) -> Pipeline:
    """
    Combine feature preprocessor and estimator into a single unified Pipeline.
    Guarantees preprocessing is fitted strictly on training data during pipeline.fit().
    """
    preprocessor = build_preprocessor(feature_columns=feature_columns)
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
    return pipeline

