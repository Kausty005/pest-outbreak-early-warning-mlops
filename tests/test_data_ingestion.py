"""Unit tests for the real-world data ingestion and alignment pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_ingestion.data_validation import (
    PHYSICAL_BOUNDS,
    validate_environmental_dataframe,
)
from src.data_ingestion.pest_surveillance_ingestion import (
    check_surveillance_data_availability,
    create_surveillance_template,
    load_pest_surveillance_data,
)
from src.data_ingestion.soil_moisture_ingestion import extract_soil_moisture_series
from src.data_ingestion.weather_ingestion import (
    IngestionConfig,
    fetch_open_meteo_weather,
    process_weather_data,
)


@pytest.fixture
def mock_open_meteo_json(tmp_path) -> dict:
    return {
        "latitude": 21.15,
        "longitude": 79.08,
        "elevation": 310.0,
        "daily": {
            "time": ["2023-07-01", "2023-07-02", "2023-07-03"],
            "temperature_2m_mean": [28.5, 29.2, 27.8],
            "temperature_2m_max": [34.0, 35.1, 32.5],
            "temperature_2m_min": [23.1, 23.5, 22.8],
            "relative_humidity_2m_mean": [75.0, 82.0, 85.0],
            "precipitation_sum": [5.2, 18.4, 42.0],
            "soil_moisture_0_to_7cm_mean": [0.28, 0.32, 0.39],
        },
    }


def test_process_weather_data_computes_rolling_features(mock_open_meteo_json):
    df = process_weather_data(mock_open_meteo_json, district="Nagpur", base_temp_gdd=10.0)

    assert len(df) == 3
    assert "observation_date" in df.columns
    assert "rainfall_7d" in df.columns
    assert "gdd_daily" in df.columns
    assert "t7_high_rh_days" in df.columns

    # Verify GDD: 28.5 - 10.0 = 18.5
    assert df.loc[0, "gdd_daily"] == 18.5
    # Verify rainfall accumulation on day 2: 5.2 + 18.4 = 23.6
    assert abs(df.loc[1, "rainfall_7d"] - 23.6) < 1e-4
    # High RH days (>= 80%): day 1 is 75% (0), day 2 is 82% (1), day 3 is 85% (2)
    assert df.loc[1, "t7_high_rh_days"] == 1
    assert df.loc[2, "t7_high_rh_days"] == 2


def test_data_validation_accepts_clean_environmental_data(mock_open_meteo_json):
    df = process_weather_data(mock_open_meteo_json, district="Nagpur")
    report = validate_environmental_dataframe(df, strict_maharashtra_bounds=True)

    assert report.is_valid is True
    assert len(report.failed_checks) == 0
    assert "GEOGRAPHIC_COORDINATES_WITHIN_BOUNDS" in report.passed_checks
    assert "THERMODYNAMIC_CONSISTENCY_PASS" in report.passed_checks


def test_data_validation_catches_thermodynamic_inconsistencies():
    # Construct invalid row where T_min > T_mean
    invalid_df = pd.DataFrame({
        "observation_date": [pd.Timestamp("2023-07-01")],
        "district": ["Nagpur"],
        "latitude": [21.15],
        "longitude": [79.08],
        "temperature_mean": [25.0],
        "temperature_min": [30.0],  # Invalid! Min > Mean
        "temperature_max": [35.0],
        "humidity_mean": [75.0],
        "rainfall_mm": [0.0],
    })
    report = validate_environmental_dataframe(invalid_df)
    assert report.is_valid is False
    assert any("THERMODYNAMIC_INCONSISTENCY" in f for f in report.failed_checks)


def test_surveillance_availability_check_on_empty_dir(tmp_path):
    audit = check_surveillance_data_availability(surveillance_dir=tmp_path)
    assert audit.status == "AWAITING_GOVERNMENT_SURVEILLANCE_DATA"
    assert audit.total_records == 0


def test_surveillance_template_generation(tmp_path):
    template_path = tmp_path / "test_template.csv"
    res_path = create_surveillance_template(output_path=template_path)
    assert res_path.exists()

    df = pd.read_csv(res_path)
    assert len(df) == 2
    assert "pest_type" in df.columns
    assert "pest_incidence_pct" in df.columns
    assert "economic_threshold_exceeded" in df.columns

