from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.ml.data_validation import (
    DataValidationError,
    audit_dataframe,
    validate_dataframe,
)

from .conftest import synthetic_frame


def test_valid_data_audit_is_complete():
    audit = audit_dataframe(synthetic_frame())
    assert audit.shape == (36, 8)
    assert audit.exact_duplicate_rows == 0
    assert audit.class_distribution == {"alpha": 12, "beta": 12, "gamma": 12}
    assert audit.duplicate_feature_rows == 0
    assert audit.near_duplicate_feature_rows == 0
    assert audit.numeric_distribution["N"]["q1"] < audit.numeric_distribution["N"]["q3"]
    assert audit.correlations["N"]["N"] == pytest.approx(1.0)


def test_audit_reports_repeated_feature_vectors_without_removing_them():
    frame = synthetic_frame()
    repeated_features = frame.iloc[[0]].copy()
    repeated_features["label"] = "beta"
    audit = audit_dataframe(pd.concat([frame, repeated_features], ignore_index=True))
    assert audit.exact_duplicate_rows == 0
    assert audit.duplicate_feature_rows == 1
    assert audit.near_duplicate_feature_rows == 1


@pytest.mark.parametrize("mutation", ["missing", "nan", "unexpected"])
def test_invalid_data_is_rejected(mutation):
    frame = synthetic_frame()
    if mutation == "missing":
        frame = frame.drop(columns="rainfall")
    elif mutation == "nan":
        frame.loc[0, "N"] = np.nan
    else:
        frame["leaked_target"] = frame["label"]
    with pytest.raises(DataValidationError):
        validate_dataframe(frame)
