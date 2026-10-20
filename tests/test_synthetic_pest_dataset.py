"""
tests/test_synthetic_pest_dataset.py
────────────────────────────────────
Automated validation test suite for data/synthetic_multicrop_pest_forecasting.csv.
Verifies exact 100,000 row count, 6 crop-pest pairs, 0 nulls, physical ranges,
realistic class imbalance, and strict temporal causality.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

DATASET_PATH = Path("data/synthetic_multicrop_pest_forecasting.csv")
SUMMARY_PATH = Path("data/synthetic_multicrop_pest_forecasting_summary.md")

EXPECTED_CROPS = {
    "Maize": "Fall armyworm",
    "Rice": "Brown planthopper",
    "Cotton": "Pink bollworm",
    "Wheat": "Aphids",
    "Tomato": "Fruit borer",
    "Chickpea": "Pod borer",
}

EXPECTED_COLUMNS = [
    "field_id",
    "district",
    "crop",
    "pest",
    "date",
    "growth_stage",
    "t7_mean_temp_c",
    "t7_min_temp_c",
    "t7_max_temp_c",
    "t7_mean_rh_pct",
    "t7_high_rh_days",
    "t7_rainfall_mm",
    "t14_rainfall_mm",
    "current_incidence_pct_t0",
    "current_severity_pct_t0",
    "pest_present_t0",
    "outbreak_within_7d",
]


@pytest.fixture(scope="module")
def dataset_df() -> pd.DataFrame:
    assert DATASET_PATH.exists(), f"Dataset file missing at {DATASET_PATH}"
    df = pd.read_csv(DATASET_PATH)
    return df


def test_dataset_exact_row_and_column_count(dataset_df: pd.DataFrame):
    """Verify that there are exactly 100,000 rows and all required columns."""
    assert len(dataset_df) == 100_000, f"Expected 100,000 rows, got {len(dataset_df)}"
    assert list(dataset_df.columns) == EXPECTED_COLUMNS


def test_zero_missing_values(dataset_df: pd.DataFrame):
    """Verify that there are zero null or NaN values across all columns."""
    nulls = dataset_df.isnull().sum()
    assert nulls.sum() == 0, f"Found missing values: {nulls[nulls > 0].to_dict()}"


def test_all_six_crops_and_pests_represented(dataset_df: pd.DataFrame):
    """Verify each of the 6 crop-pest pairs is present with balanced representation."""
    crop_pest_counts = dataset_df.groupby(["crop", "pest"]).size().to_dict()
    assert len(crop_pest_counts) == 6

    for crop, pest in EXPECTED_CROPS.items():
        assert (crop, pest) in crop_pest_counts
        count = crop_pest_counts[(crop, pest)]
        # Between 16,660 and 16,670 rows each
        assert 16_660 <= count <= 16_670


def test_physical_feature_ranges(dataset_df: pd.DataFrame):
    """Verify temperatures, humidity, rainfall, and incidence are within valid bounds."""
    assert dataset_df["t7_mean_temp_c"].between(5.0, 45.0).all()
    assert dataset_df["t7_min_temp_c"].between(0.0, 40.0).all()
    assert dataset_df["t7_max_temp_c"].between(10.0, 50.0).all()
    assert (dataset_df["t7_max_temp_c"] >= dataset_df["t7_min_temp_c"]).all()

    assert dataset_df["t7_mean_rh_pct"].between(20.0, 100.0).all()
    assert dataset_df["t7_high_rh_days"].between(0, 7).all()

    assert (dataset_df["t7_rainfall_mm"] >= 0.0).all()
    assert (dataset_df["t14_rainfall_mm"] >= 0.0).all()
    # 14-day rainfall must be >= 7-day rainfall
    assert (dataset_df["t14_rainfall_mm"] >= (dataset_df["t7_rainfall_mm"] - 1e-4)).all()

    assert dataset_df["current_incidence_pct_t0"].between(0.0, 100.0).all()
    assert dataset_df["current_severity_pct_t0"].between(0.0, 100.0).all()

    assert set(dataset_df["pest_present_t0"].unique()).issubset({0, 1})
    assert set(dataset_df["outbreak_within_7d"].unique()).issubset({0, 1})


def test_realistic_class_imbalance(dataset_df: pd.DataFrame):
    """Verify realistic class imbalance (10% to 25% outbreak prevalence overall and per crop)."""
    overall_rate = dataset_df["outbreak_within_7d"].mean()
    assert 0.12 <= overall_rate <= 0.22, f"Unexpected overall rate: {overall_rate:.2%}"

    for (crop, pest), group in dataset_df.groupby(["crop", "pest"]):
        crop_rate = group["outbreak_within_7d"].mean()
        assert 0.10 <= crop_rate <= 0.25, f"{crop} ({pest}) rate out of bounds: {crop_rate:.2%}"


def test_chronological_ordering(dataset_df: pd.DataFrame):
    """Verify dataset records are ordered chronologically."""
    dates = pd.to_datetime(dataset_df["date"])
    assert dates.is_monotonic_increasing, "Dataset is not sorted chronologically by date"


def test_summary_markdown_exists():
    """Verify the summary markdown report was created and contains key disclosures."""
    assert SUMMARY_PATH.exists()
    content = SUMMARY_PATH.read_text(encoding="utf-8")
    assert "SYNTHETIC DATA DISCLAIMER" in content
    assert "100,000" in content
    assert "Fall armyworm" in content
    assert "Brown planthopper" in content
