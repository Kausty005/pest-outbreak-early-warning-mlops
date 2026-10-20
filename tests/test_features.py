from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import ExtraTreesClassifier

from backend.ml.feature_engineering import (
    CropFeatureBuilder,
    FeatureConfig,
    make_model_pipeline,
)


def test_engineered_feature_formulas_and_categories():
    source = pd.DataFrame([{"N": 10, "P": 5, "K": 2, "temperature": 20, "humidity": 50, "ph": 6.5, "rainfall": 100}])
    actual = CropFeatureBuilder(enabled=True).fit_transform(source).iloc[0]
    assert actual["npk_total"] == 17
    assert actual["nitrogen_phosphorus_ratio"] == 2
    assert actual["nitrogen_potassium_ratio"] == 5
    assert actual["phosphorus_potassium_ratio"] == 2.5
    assert actual["temperature_humidity_interaction"] == 10
    assert actual["ph_category"] == "near_neutral"
    assert actual["rainfall_category"] == "medium"


def test_zero_denominators_are_safe():
    source = pd.DataFrame([{"N": 10, "P": 0, "K": 0, "temperature": 20, "humidity": 50, "ph": 6, "rainfall": 20}])
    actual = CropFeatureBuilder(enabled=True).fit_transform(source)
    assert actual.loc[0, "nitrogen_phosphorus_ratio"] == 0
    assert actual.loc[0, "nitrogen_potassium_ratio"] == 0
    assert actual.loc[0, "phosphorus_potassium_ratio"] == 0
    assert np.isfinite(actual[["nitrogen_phosphorus_ratio", "nitrogen_potassium_ratio", "phosphorus_potassium_ratio"]].to_numpy()).all()


def test_baseline_and_engineered_have_consistent_input_contract(synthetic_frame):
    X, y = synthetic_frame[["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]], synthetic_frame["label"]
    baseline = make_model_pipeline(ExtraTreesClassifier(n_estimators=5, random_state=42), FeatureConfig(enabled=False)).fit(X, y)
    engineered = make_model_pipeline(ExtraTreesClassifier(n_estimators=5, random_state=42), FeatureConfig(enabled=True)).fit(X, y)
    assert baseline.predict(X).shape == engineered.predict(X).shape == (len(X),)


def test_invalid_feature_shape_is_rejected():
    with pytest.raises(ValueError, match="missing required features"):
        CropFeatureBuilder().fit(pd.DataFrame({"N": [1]}))
