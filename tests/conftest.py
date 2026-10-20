from __future__ import annotations

import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from backend.ml.data_validation import FEATURE_COLUMNS
from backend.ml.feature_engineering import FeatureConfig, make_model_pipeline


def synthetic_frame(rows_per_class: int = 12) -> pd.DataFrame:
    """Synthetic numeric fixture solely for test execution; never agricultural source data."""
    rows = []
    for class_index, label in enumerate(("alpha", "beta", "gamma")):
        for offset in range(rows_per_class):
            rows.append(
                {
                    "N": class_index * 35 + offset,
                    "P": class_index * 20 + offset + 5,
                    "K": class_index * 10 + offset + 5,
                    "temperature": 18 + class_index * 8 + offset * 0.1,
                    "humidity": 40 + class_index * 15 + offset * 0.2,
                    "ph": 5 + class_index + offset * 0.02,
                    "rainfall": 30 + class_index * 90 + offset,
                    "label": label,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(name="synthetic_frame")
def synthetic_frame_fixture():
    return synthetic_frame()


@pytest.fixture
def fitted_model():
    frame = synthetic_frame()
    pipeline = make_model_pipeline(RandomForestClassifier(n_estimators=10, random_state=42), FeatureConfig(enabled=True))
    pipeline.fit(frame[FEATURE_COLUMNS], frame["label"])
    return pipeline
