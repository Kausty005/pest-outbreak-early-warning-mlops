"""Dataset contracts and auditable validation for the crop classifier."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET_COLUMN = "label"
REQUIRED_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN]


class DataValidationError(ValueError):
    """Raised when a dataset does not satisfy the model input contract."""


@dataclass(frozen=True)
class DatasetAudit:
    shape: tuple[int, int]
    columns: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    exact_duplicate_rows: int
    class_distribution: dict[str, int]
    numeric_ranges: dict[str, dict[str, float]]
    numeric_distribution: dict[str, dict[str, float]]
    correlations: dict[str, dict[str, float]]
    duplicate_feature_rows: int
    near_duplicate_feature_rows: int
    checksum_sha256: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate source columns and values without imputing or removing records."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    unexpected_columns = [column for column in frame.columns if column not in REQUIRED_COLUMNS]
    if missing_columns or unexpected_columns:
        raise DataValidationError(
            f"Expected exactly {REQUIRED_COLUMNS}; missing={missing_columns}, unexpected={unexpected_columns}"
        )
    if frame.empty:
        raise DataValidationError("Dataset has no rows")
    if frame[REQUIRED_COLUMNS].isna().any().any():
        missing = frame[REQUIRED_COLUMNS].isna().sum()
        raise DataValidationError(f"Dataset contains missing values: {missing[missing > 0].to_dict()}")

    validated = frame.copy()
    for column in FEATURE_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
        values = validated[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise DataValidationError(f"Column {column!r} contains non-finite values")
    validated[TARGET_COLUMN] = validated[TARGET_COLUMN].astype(str).str.strip()
    if (validated[TARGET_COLUMN] == "").any():
        raise DataValidationError("Target label contains blank values")
    if validated[TARGET_COLUMN].nunique() < 2:
        raise DataValidationError("At least two crop classes are required")
    return validated[REQUIRED_COLUMNS]


def audit_dataframe(frame: pd.DataFrame, checksum: str | None = None) -> DatasetAudit:
    validated = validate_dataframe(frame)
    ranges = {
        column: {
            "min": float(validated[column].min()),
            "max": float(validated[column].max()),
            "mean": float(validated[column].mean()),
        }
        for column in FEATURE_COLUMNS
    }
    numeric_distribution = {
        column: {
            "median": float(validated[column].median()),
            "std": float(validated[column].std()),
            "q1": float(validated[column].quantile(0.25)),
            "q3": float(validated[column].quantile(0.75)),
        }
        for column in FEATURE_COLUMNS
    }
    # This is an auditable screen, not a reason to discard observations.  The
    # one-decimal comparison deliberately matches the dataset-inspection report
    # and gives operators a simple, reproducible near-duplicate signal.
    rounded_features = validated.loc[:, FEATURE_COLUMNS].round(1)
    return DatasetAudit(
        shape=(int(validated.shape[0]), int(validated.shape[1])),
        columns=list(validated.columns),
        dtypes={key: str(value) for key, value in validated.dtypes.items()},
        missing_values={key: int(value) for key, value in validated.isna().sum().items()},
        exact_duplicate_rows=int(validated.duplicated().sum()),
        class_distribution={key: int(value) for key, value in validated[TARGET_COLUMN].value_counts().sort_index().items()},
        numeric_ranges=ranges,
        numeric_distribution=numeric_distribution,
        correlations={
            row: {column: float(value) for column, value in values.items()}
            for row, values in validated.loc[:, FEATURE_COLUMNS].corr().to_dict().items()
        },
        duplicate_feature_rows=int(validated.duplicated(subset=FEATURE_COLUMNS).sum()),
        near_duplicate_feature_rows=int(rounded_features.duplicated().sum()),
        checksum_sha256=checksum,
    )


def load_valid_dataset(path: str | Path) -> tuple[pd.DataFrame, DatasetAudit]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Dataset not found: {source}")
    frame = pd.read_csv(source)
    validated = validate_dataframe(frame)
    return validated, audit_dataframe(validated, sha256_file(source))
