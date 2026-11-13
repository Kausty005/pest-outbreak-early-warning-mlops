"""
src/pest_forecasting/dataset.py
───────────────────────────────
Data loading, schema validation, and leakage-safe chronological splitting
for the experimental synthetic multi-crop pest forecasting pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

TARGET_COLUMN = "outbreak_within_7d"
METADATA_COLUMNS = ["field_id", "date"]

CATEGORICAL_COLUMNS = [
    "district",
    "crop",
    "pest",
    "growth_stage",
]

# Weather / Environmental features (causally available prior to outbreak)
ENVIRONMENTAL_NUMERICAL_CONTINUOUS = [
    "t7_mean_temp_c",
    "t7_min_temp_c",
    "t7_max_temp_c",
    "t7_mean_rh_pct",
    "t7_rainfall_mm",
    "t14_rainfall_mm",
]

ENVIRONMENTAL_NUMERICAL_DISCRETE = [
    "t7_high_rh_days",
]

ENVIRONMENTAL_NUMERICAL_COLUMNS = ENVIRONMENTAL_NUMERICAL_CONTINUOUS + ENVIRONMENTAL_NUMERICAL_DISCRETE
ENVIRONMENTAL_FEATURE_COLUMNS = CATEGORICAL_COLUMNS + ENVIRONMENTAL_NUMERICAL_COLUMNS

# In-field scouting observations (only available after infestation / scouting inspection)
SCOUTING_NUMERICAL_CONTINUOUS = [
    "current_incidence_pct_t0",
    "current_severity_pct_t0",
]

SCOUTING_NUMERICAL_DISCRETE = [
    "pest_present_t0",
]

SCOUTING_FEATURE_COLUMNS = SCOUTING_NUMERICAL_CONTINUOUS + SCOUTING_NUMERICAL_DISCRETE

# Full feature configuration (all 14 features)
FULL_FEATURE_COLUMNS = ENVIRONMENTAL_FEATURE_COLUMNS + SCOUTING_FEATURE_COLUMNS

ALL_COLUMNS = METADATA_COLUMNS + FULL_FEATURE_COLUMNS + [TARGET_COLUMN]


class DataValidationError(ValueError):
    """Raised when dataset fails schema, range, or causal validation."""
    pass


class DataLeakageError(RuntimeError):
    """Raised when leakage across features or splits is detected."""
    pass


@dataclass
class DatasetSplits:
    """Container for features and labels across train, val, and test splits."""
    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series

    meta_train: pd.DataFrame
    meta_val: pd.DataFrame
    meta_test: pd.DataFrame


@dataclass
class SplitMetadata:
    """Summary of split sizes, date ranges, and purge embargo counts."""
    feature_configuration: str
    train_start_date: str
    train_end_date: str
    train_count: int
    train_outbreak_count: int
    train_outbreak_rate: float

    val_start_date: str
    val_end_date: str
    val_count: int
    val_outbreak_count: int
    val_outbreak_rate: float

    test_start_date: str
    test_end_date: str
    test_count: int
    test_outbreak_count: int
    test_outbreak_rate: float

    purged_gap1_count: int
    purged_gap2_count: int
    total_purged_count: int
    purge_days: int


def verify_no_leakage(feature_list: Sequence[str]) -> None:
    """
    Verify that forbidden columns (target, date, field_id) and target-derived
    or future observation columns are strictly excluded from predictive features.
    """
    forbidden = {
        TARGET_COLUMN,
        "date",
        "field_id",
        "future_incidence",
        "future_severity",
        "future_temp",
        "future_rh",
        "future_rainfall",
    }
    for col in feature_list:
        if col in forbidden:
            raise DataLeakageError(
                f"Data leakage detected! Forbidden column '{col}' found in feature list."
            )
        if "future" in col.lower() or "outbreak" in col.lower() or "target" in col.lower():
            raise DataLeakageError(
                f"Data leakage detected! Suspicious future/target-derived column '{col}'."
            )


def load_and_validate_dataset(
    csv_path: str | Path,
    expected_rows: int | None = 100000,
) -> pd.DataFrame:
    """
    Load dataset from CSV and execute strict quality, schema, and range checks.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found at: {path}")

    df = pd.read_csv(path)

    # 1. Row count validation
    if expected_rows is not None and len(df) != expected_rows:
        raise DataValidationError(
            f"Expected {expected_rows} rows, but found {len(df)} rows."
        )

    # 2. Column presence validation
    missing_cols = [c for c in ALL_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")

    # 3. Missing values check
    null_counts = df[ALL_COLUMNS].isnull().sum()
    if null_counts.sum() > 0:
        bad_cols = null_counts[null_counts > 0].to_dict()
        raise DataValidationError(f"Null / missing values found in columns: {bad_cols}")

    # 4. Target values check
    unique_targets = set(df[TARGET_COLUMN].unique())
    if not unique_targets.issubset({0, 1}):
        raise DataValidationError(
            f"Target {TARGET_COLUMN} must be restricted to {{0, 1}}, got {unique_targets}"
        )

    # 5. Date parsing validation
    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception as exc:
        raise DataValidationError(f"Invalid date format in dataset: {exc}") from exc

    # 6. Physical feature range checks
    if (df["t7_min_temp_c"] > df["t7_max_temp_c"]).any():
        raise DataValidationError("t7_min_temp_c cannot exceed t7_max_temp_c.")

    if ((df["t7_mean_rh_pct"] < 0) | (df["t7_mean_rh_pct"] > 100)).any():
        raise DataValidationError("t7_mean_rh_pct must be bounded within [0, 100].")

    if (df["t7_rainfall_mm"] < 0).any() or (df["t14_rainfall_mm"] < 0).any():
        raise DataValidationError("Rainfall features cannot be negative.")

    if (df["t7_rainfall_mm"] > df["t14_rainfall_mm"]).any():
        raise DataValidationError("7-day rainfall cannot exceed 14-day cumulative rainfall.")

    return df


def chronological_split_with_purging(
    df: pd.DataFrame,
    feature_set: str = "full",  # "full" or "environmental"
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    purge_days: int = 7,
) -> tuple[DatasetSplits, SplitMetadata]:
    """
    Split time-series observations into Train, Validation, and Test partitions
    strictly chronologically, enforcing a multi-day purge embargo between splits.

    PURGE EMBARGO RATIONALE:
    The target label `outbreak_within_7d` is calculated over the forward 7-day window [t0+1, t0+7].
    If the training split ends on date T_train_end, its last sample inspects up to
    T_train_end + 7. By starting the validation split at T_train_end + (purge_days + 1),
    no training sample evaluates future field conditions that fall inside the validation period.
    """
    if df.empty:
        raise ValueError("Cannot split an empty dataframe.")

    # Select feature columns
    if feature_set.lower() in ("environmental", "environmental_only", "weather"):
        selected_features = list(ENVIRONMENTAL_FEATURE_COLUMNS)
        config_name = "ENVIRONMENTAL_ONLY"
    elif feature_set.lower() in ("full", "full_synthetic"):
        selected_features = list(FULL_FEATURE_COLUMNS)
        config_name = "FULL_SYNTHETIC"
    else:
        raise ValueError(f"Unknown feature_set '{feature_set}'. Must be 'full' or 'environmental'.")

    verify_no_leakage(selected_features)

    # Ensure chronological order
    df_sorted = df.sort_values(by="date").reset_index(drop=True)
    n = len(df_sorted)

    # Determine boundary dates based on target proportions
    train_cutoff_idx = int(n * train_ratio)
    val_cutoff_idx = int(n * (train_ratio + val_ratio))

    date_train_end = df_sorted.iloc[train_cutoff_idx - 1]["date"]
    date_val_start = date_train_end + pd.Timedelta(days=purge_days + 1)

    date_val_end = df_sorted.iloc[val_cutoff_idx - 1]["date"]
    if date_val_end < date_val_start:
        date_val_end = date_val_start + pd.Timedelta(days=30)
    date_test_start = date_val_end + pd.Timedelta(days=purge_days + 1)

    # Build masks
    mask_train = df_sorted["date"] <= date_train_end
    mask_gap1 = (df_sorted["date"] > date_train_end) & (df_sorted["date"] < date_val_start)
    mask_val = (df_sorted["date"] >= date_val_start) & (df_sorted["date"] <= date_val_end)
    mask_gap2 = (df_sorted["date"] > date_val_end) & (df_sorted["date"] < date_test_start)
    mask_test = df_sorted["date"] >= date_test_start

    train_df = df_sorted[mask_train].copy()
    val_df = df_sorted[mask_val].copy()
    test_df = df_sorted[mask_test].copy()

    purged_gap1 = int(mask_gap1.sum())
    purged_gap2 = int(mask_gap2.sum())

    if train_df.empty or val_df.empty or test_df.empty:
        raise ValueError(
            f"Dataset date range is too narrow to split into train, val, and test partitions "
            f"with a {purge_days}-day purge gap. Found train={len(train_df)}, val={len(val_df)}, test={len(test_df)}."
        )

    # Leakage check: verify no overlap in dates
    assert train_df["date"].max() < val_df["date"].min(), "Train and Val dates overlap!"
    assert val_df["date"].max() < test_df["date"].min(), "Val and Test dates overlap!"

    # Purge window verification: target horizon is 7 days
    target_horizon_days = 7
    train_max_target_date = train_df["date"].max() + pd.Timedelta(days=target_horizon_days)
    val_min_obs_date = val_df["date"].min()
    if train_max_target_date >= val_min_obs_date:
        raise DataLeakageError(
            f"Purge gap insufficient! Train forward window ends {train_max_target_date.date()}, "
            f"but Val starts {val_min_obs_date.date()}."
        )

    val_max_target_date = val_df["date"].max() + pd.Timedelta(days=target_horizon_days)
    test_min_obs_date = test_df["date"].min()
    if val_max_target_date >= test_min_obs_date:
        raise DataLeakageError(
            f"Purge gap insufficient! Val forward window ends {val_max_target_date.date()}, "
            f"but Test starts {test_min_obs_date.date()}."
        )

    # Separate X and y
    X_train = train_df[selected_features].copy()
    y_train = train_df[TARGET_COLUMN].copy().astype(int)
    meta_train = train_df[METADATA_COLUMNS].copy()

    X_val = val_df[selected_features].copy()
    y_val = val_df[TARGET_COLUMN].copy().astype(int)
    meta_val = val_df[METADATA_COLUMNS].copy()

    X_test = test_df[selected_features].copy()
    y_test = test_df[TARGET_COLUMN].copy().astype(int)
    meta_test = test_df[METADATA_COLUMNS].copy()

    splits = DatasetSplits(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        meta_train=meta_train,
        meta_val=meta_val,
        meta_test=meta_test,
    )

    metadata = SplitMetadata(
        feature_configuration=config_name,
        train_start_date=str(train_df["date"].min().date()),
        train_end_date=str(train_df["date"].max().date()),
        train_count=len(train_df),
        train_outbreak_count=int(y_train.sum()),
        train_outbreak_rate=float(y_train.mean()),
        val_start_date=str(val_df["date"].min().date()),
        val_end_date=str(val_df["date"].max().date()),
        val_count=len(val_df),
        val_outbreak_count=int(y_val.sum()),
        val_outbreak_rate=float(y_val.mean()),
        test_start_date=str(test_df["date"].min().date()),
        test_end_date=str(test_df["date"].max().date()),
        test_count=len(test_df),
        test_outbreak_count=int(y_test.sum()),
        test_outbreak_rate=float(y_test.mean()),
        purged_gap1_count=purged_gap1,
        purged_gap2_count=purged_gap2,
        total_purged_count=purged_gap1 + purged_gap2,
        purge_days=purge_days,
    )

    return splits, metadata

