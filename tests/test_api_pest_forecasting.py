"""
tests/test_api_pest_forecasting.py
──────────────────────────────────
Integration tests for FastAPI Pest Outbreak Forecasting Endpoints:
- GET /api/v1/pest-forecasting/model-info
- GET /api/v1/pest-forecasting/example
- POST /api/v1/pest-forecasting/predict (ENVIRONMENTAL_ONLY and SCOUTING_ASSISTED)
- Validation error handling and scientific disclaimers
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_pest_forecasting_model_info_endpoint():
    """Verify metadata endpoint returns active model version and experimental status."""
    resp = client.get("/api/v1/pest-forecasting/model-info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service_status"] == "ok"
    assert data["environmental_model_available"] is True
    assert data["scouting_model_available"] is True
    assert data["classification"] == "SYNTHETIC_EXPERIMENTAL"
    assert data["is_production_ready"] is False
    assert data["production_readiness_status"] == "BLOCKED"
    assert "environmental" in data["decision_thresholds"]
    assert "scouting_assisted" in data["decision_thresholds"]
    assert "SYNTHETIC EXPERIMENTAL MODEL ONLY" in data["disclaimer"]


def test_pest_forecasting_example_endpoint():
    """Verify example generator returns valid payloads for both configurations."""
    # 1. Environmental only example
    r_env = client.get("/api/v1/pest-forecasting/example?configuration=ENVIRONMENTAL_ONLY")
    assert r_env.status_code == 200
    data_env = r_env.json()
    assert data_env["configuration"] == "ENVIRONMENTAL_ONLY"
    assert "t7_mean_temp_c" in data_env
    assert "t7_mean_soil_moisture" in data_env

    # 2. Scouting assisted example
    r_scout = client.get("/api/v1/pest-forecasting/example?configuration=SCOUTING_ASSISTED")
    assert r_scout.status_code == 200
    data_scout = r_scout.json()
    assert data_scout["configuration"] == "SCOUTING_ASSISTED"
    assert "scout_incidence_pct" in data_scout
    assert "pest_present" in data_scout


def test_predict_environmental_only_success():
    """Verify successful 7-day inference using only environmental features."""
    payload = {
        "configuration": "ENVIRONMENTAL_ONLY",
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Squaring",
        "t7_mean_temp_c": 32.0,
        "t7_min_temp_c": 26.0,
        "t7_max_temp_c": 37.0,
        "t7_mean_rh_pct": 79.0,
        "t7_rainfall_mm": 15.0,
        "t14_rainfall_mm": 50.0,
        "t7_mean_soil_moisture": 0.40,
        "t7_high_rh_days": 4,
        "t7_consecutive_dry_days": 2,
    }
    resp = client.post("/api/v1/pest-forecasting/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["classification"] == "SYNTHETIC_EXPERIMENTAL"
    assert data["is_production_ready"] is False
    assert data["feature_configuration"] == "ENVIRONMENTAL_ONLY"
    assert 0.0 <= data["outbreak_risk_probability"] <= 1.0
    assert isinstance(data["outbreak_warning"], bool)
    assert data["prediction_horizon_days"] == 7
    assert data["decision_threshold"] > 0.0
    assert "SYNTHETIC EXPERIMENTAL MODEL ONLY" in data["disclaimer"]
    assert data["input_summary"]["crop"] == "Cotton"


def test_predict_scouting_assisted_success():
    """Verify successful 7-day inference including in-field scouting observations."""
    payload = {
        "configuration": "SCOUTING_ASSISTED",
        "crop": "Rice",
        "pest": "Brown planthopper",
        "district": "Wardha",
        "growth_stage": "Stem Elongation",
        "t7_mean_temp_c": 29.5,
        "t7_min_temp_c": 24.0,
        "t7_max_temp_c": 34.0,
        "t7_mean_rh_pct": 85.0,
        "t7_rainfall_mm": 35.0,
        "t14_rainfall_mm": 80.0,
        "t7_mean_soil_moisture": 0.45,
        "t7_high_rh_days": 5,
        "t7_consecutive_dry_days": 1,
        "scout_incidence_pct": 22.0,
        "scout_severity_pct": 12.0,
        "trap_catch_count": 35.0,
        "days_since_scouting": 2.0,
        "pest_present": 1,
    }
    resp = client.post("/api/v1/pest-forecasting/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["feature_configuration"] == "SCOUTING_ASSISTED"
    assert 0.0 <= data["outbreak_risk_probability"] <= 1.0
    assert "SYNTHETIC EXPERIMENTAL MODEL ONLY" in data["disclaimer"]


def test_predict_rejects_missing_scouting_fields_in_scouting_mode():
    """Verify that SCOUTING_ASSISTED mode rejects requests missing required scouting fields."""
    payload = {
        "configuration": "SCOUTING_ASSISTED",
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Squaring",
        "t7_mean_temp_c": 32.0,
        "t7_min_temp_c": 26.0,
        "t7_max_temp_c": 37.0,
        "t7_mean_rh_pct": 79.0,
        "t7_rainfall_mm": 15.0,
        "t14_rainfall_mm": 50.0,
        "t7_mean_soil_moisture": 0.40,
        "t7_high_rh_days": 4,
        "t7_consecutive_dry_days": 2,
        # Intentionally omitting scout_incidence_pct, etc.
    }
    resp = client.post("/api/v1/pest-forecasting/predict", json=payload)
    assert resp.status_code == 422  # Pydantic validation failure


def test_predict_rejects_physical_inconsistencies():
    """Verify physical bounds validation catches inconsistent temperatures and rainfalls."""
    # 1. Min temp > Max temp
    payload_temp = {
        "configuration": "ENVIRONMENTAL_ONLY",
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Squaring",
        "t7_mean_temp_c": 32.0,
        "t7_min_temp_c": 40.0,  # Invalid: min > max
        "t7_max_temp_c": 30.0,
        "t7_mean_rh_pct": 79.0,
        "t7_rainfall_mm": 15.0,
        "t14_rainfall_mm": 50.0,
        "t7_mean_soil_moisture": 0.40,
        "t7_high_rh_days": 4,
        "t7_consecutive_dry_days": 2,
    }
    r1 = client.post("/api/v1/pest-forecasting/predict", json=payload_temp)
    assert r1.status_code == 422

    # 2. 7-day rainfall > 14-day cumulative rainfall
    payload_rain = {
        "configuration": "ENVIRONMENTAL_ONLY",
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Squaring",
        "t7_mean_temp_c": 32.0,
        "t7_min_temp_c": 25.0,
        "t7_max_temp_c": 35.0,
        "t7_mean_rh_pct": 79.0,
        "t7_rainfall_mm": 60.0,   # Invalid: 7d rain > 14d rain
        "t14_rainfall_mm": 40.0,
        "t7_mean_soil_moisture": 0.40,
        "t7_high_rh_days": 4,
        "t7_consecutive_dry_days": 2,
    }
    r2 = client.post("/api/v1/pest-forecasting/predict", json=payload_rain)
    assert r2.status_code == 422
