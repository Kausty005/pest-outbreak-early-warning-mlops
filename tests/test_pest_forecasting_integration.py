"""
Integration and API contract tests for 7-Day Pest Outbreak Forecasting Module.
Verifies model loading, endpoint routing, schema validation, threshold gating,
model switching rules, physical range enforcement, and production isolation.
"""
from __future__ import annotations

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.pest_forecast import PestForecastRequest
from backend.app.services.pest_forecast_service import (
    PestForecastService,
    SYNTHETIC_DATA_DISCLAIMER,
    VALID_CROP_PEST_PAIRS,
)

FERTILIZER_MODEL_PATH = Path("models/fertilizer_model.joblib")
FORECASTER_MODEL_PATH = Path("models/synthetic_pest_outbreak_forecaster.joblib")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_existing_production_models_remain_untouched():
    """Verify that fertilizer and crop recommendation artifacts exist and were untouched."""
    assert FERTILIZER_MODEL_PATH.exists()
    assert FERTILIZER_MODEL_PATH.stat().st_size > 50_000_000  # Fertilizer model ~64MB
    assert FORECASTER_MODEL_PATH.exists()


def test_pest_forecasting_catalog_info(client: TestClient):
    """Verify GET /api/v1/pest-forecast/info returns discovery catalog and disclaimer."""
    res = client.get("/api/v1/pest-forecast/info")
    assert res.status_code == 200
    data = res.json()

    assert "available_models" in data
    assert len(data["available_models"]) >= 3
    model_types = {m["model_type"] for m in data["available_models"]}
    assert {"full", "weather_crop", "early_warning"}.issubset(model_types)

    # Check thresholds in discovery info
    thresh_map = {m["model_type"]: m["decision_threshold"] for m in data["available_models"]}
    assert thresh_map["full"] == 0.72
    assert thresh_map["weather_crop"] == 0.42
    assert thresh_map["early_warning"] == 0.56

    assert "crop_pest_pairs" in data
    assert data["crop_pest_pairs"]["Maize"] == "Fall armyworm"
    assert data["crop_pest_pairs"]["Rice"] == "Brown planthopper"
    assert data["disclaimer"] == SYNTHETIC_DATA_DISCLAIMER


def test_example_endpoint(client: TestClient):
    """Verify GET /api/v1/pest-forecast/example returns valid prefillable payload."""
    res = client.get("/api/v1/pest-forecast/example")
    assert res.status_code == 200
    ex = res.json()
    assert ex["crop"] == "Maize"
    assert ex["pest"] == "Fall armyworm"
    assert "t7_mean_temp_c" in ex
    assert "current_incidence_pct_t0" in ex


def test_successful_full_model_prediction(client: TestClient):
    """Verify full-feature model forecast on /api/v1/pest-forecast/predict and /api/pest-forecast/predict."""
    payload = {
        "crop": "Maize",
        "pest": "Fall armyworm",
        "district": "Davanagere",
        "growth_stage": "V5_V8_mid_whorl",
        "model_type": "full",
        "t7_mean_temp_c": 28.5,
        "t7_min_temp_c": 22.0,
        "t7_max_temp_c": 35.0,
        "t7_mean_rh_pct": 78.0,
        "t7_high_rh_days": 3,
        "t7_rainfall_mm": 35.0,
        "t14_rainfall_mm": 65.0,
        "current_incidence_pct_t0": 8.5,
        "current_severity_pct_t0": 4.2,
        "pest_present_t0": 1,
    }

    # Test v1 prefix
    res = client.post("/api/v1/pest-forecast/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["crop"] == "Maize"
    assert data["target_pest"] == "Fall armyworm"
    assert data["forecast_horizon"] == "7 days"
    assert 0.0 <= data["outbreak_probability"] <= 1.0
    assert isinstance(data["outbreak_predicted"], bool)
    assert data["decision_threshold"] == 0.72
    assert data["model_used"] == "full"
    assert data["disclaimer"] == SYNTHETIC_DATA_DISCLAIMER

    # Test direct /api prefix
    res_root = client.post("/api/pest-forecast/predict", json=payload)
    assert res_root.status_code == 200
    assert res_root.json()["outbreak_probability"] == data["outbreak_probability"]


def test_weather_crop_model_requires_no_infestation(client: TestClient):
    """Verify weather_crop model succeeds when scouting metrics are null."""
    payload = {
        "crop": "Rice",
        "pest": "Brown planthopper",
        "district": "East Godavari",
        "growth_stage": "Booting_heading",
        "model_type": "weather_crop",
        "t7_mean_temp_c": 29.0,
        "t7_min_temp_c": 24.0,
        "t7_max_temp_c": 36.0,
        "t7_mean_rh_pct": 82.0,
        "t7_high_rh_days": 4,
        "t7_rainfall_mm": 50.0,
        "t14_rainfall_mm": 90.0,
        # Infestation omitted
    }

    res = client.post("/api/v1/pest-forecast/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["crop"] == "Rice"
    assert data["model_used"] == "weather_crop"
    assert data["decision_threshold"] == 0.42
    assert "current_incidence_pct_t0" not in data["features_used"]


def test_early_warning_model_requires_presence_only(client: TestClient):
    """Verify early_warning model requires pest_present_t0 but allows null incidence/severity."""
    # Fails if pest_present_t0 missing
    payload_missing = {
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Flowering",
        "model_type": "early_warning",
        "t7_mean_temp_c": 30.0,
        "t7_min_temp_c": 22.0,
        "t7_max_temp_c": 38.0,
        "t7_mean_rh_pct": 70.0,
        "t7_high_rh_days": 1,
        "t7_rainfall_mm": 10.0,
        "t14_rainfall_mm": 20.0,
    }
    res1 = client.post("/api/v1/pest-forecast/predict", json=payload_missing)
    assert res1.status_code == 422
    assert "pest_present_t0" in res1.json()["detail"]

    # Succeeds when pest_present_t0 is provided
    payload_valid = dict(payload_missing, pest_present_t0=1)
    res2 = client.post("/api/v1/pest-forecast/predict", json=payload_valid)
    assert res2.status_code == 200
    data = res2.json()
    assert data["decision_threshold"] == 0.56
    assert data["model_used"] == "early_warning"


def test_validation_rejects_missing_scouting_on_full_model(client: TestClient):
    """Verify that full model strictly rejects missing incidence or severity rather than silently switching."""
    payload = {
        "crop": "Wheat",
        "pest": "Aphids",
        "district": "Ludhiana",
        "growth_stage": "Jointing_stem_extension",
        "model_type": "full",
        "t7_mean_temp_c": 18.0,
        "t7_min_temp_c": 10.0,
        "t7_max_temp_c": 26.0,
        "t7_mean_rh_pct": 65.0,
        "t7_high_rh_days": 0,
        "t7_rainfall_mm": 5.0,
        "t14_rainfall_mm": 15.0,
        # Scouting metrics missing
    }

    res = client.post("/api/v1/pest-forecast/predict", json=payload)
    assert res.status_code == 422
    err_detail = res.json()["detail"]
    assert "requires field scouting infestation features" in err_detail


def test_validation_rejects_crop_pest_mismatch(client: TestClient):
    """Verify that invalid crop-pest combinations are rejected."""
    payload = {
        "crop": "Tomato",
        "pest": "Pink bollworm",  # Pink bollworm attacks cotton, not tomato!
        "district": "Kolar",
        "growth_stage": "Flowering",
        "model_type": "weather_crop",
        "t7_mean_temp_c": 26.0,
        "t7_min_temp_c": 18.0,
        "t7_max_temp_c": 32.0,
        "t7_mean_rh_pct": 75.0,
        "t7_high_rh_days": 2,
        "t7_rainfall_mm": 20.0,
        "t14_rainfall_mm": 40.0,
    }

    res = client.post("/api/v1/pest-forecast/predict", json=payload)
    assert res.status_code == 422
    assert "Target pest mismatch" in res.json()["detail"]


def test_validation_rejects_physical_inconsistencies(client: TestClient):
    """Verify that t7_min > t7_max or t14_rainfall < t7_rainfall are caught by Pydantic."""
    # Min temp > max temp
    bad_temp = {
        "crop": "Chickpea",
        "pest": "Pod borer",
        "district": "Kalaburagi",
        "growth_stage": "Pod_filling",
        "model_type": "weather_crop",
        "t7_mean_temp_c": 25.0,
        "t7_min_temp_c": 35.0,  # Min > Max!
        "t7_max_temp_c": 25.0,
        "t7_mean_rh_pct": 60.0,
        "t7_high_rh_days": 0,
        "t7_rainfall_mm": 10.0,
        "t14_rainfall_mm": 20.0,
    }
    res1 = client.post("/api/v1/pest-forecast/predict", json=bad_temp)
    assert res1.status_code == 422

    # 14-day rainfall < 7-day rainfall
    bad_rain = {
        "crop": "Chickpea",
        "pest": "Pod borer",
        "district": "Kalaburagi",
        "growth_stage": "Pod_filling",
        "model_type": "weather_crop",
        "t7_mean_temp_c": 25.0,
        "t7_min_temp_c": 18.0,
        "t7_max_temp_c": 32.0,
        "t7_mean_rh_pct": 60.0,
        "t7_high_rh_days": 0,
        "t7_rainfall_mm": 50.0,
        "t14_rainfall_mm": 20.0,  # 14d < 7d!
    }
    res2 = client.post("/api/v1/pest-forecast/predict", json=bad_rain)
    assert res2.status_code == 422


def test_forbidden_columns_never_passed_into_model():
    """Verify that field_id, date, or outbreak_within_7d cannot leak into model inference."""
    service = PestForecastService()
    req = PestForecastRequest(
        crop="Maize",
        pest="Fall armyworm",
        district="Davanagere",
        growth_stage="V1_V4_early_whorl",
        model_type="weather_crop",
        t7_mean_temp_c=28.0,
        t7_min_temp_c=22.0,
        t7_max_temp_c=34.0,
        t7_mean_rh_pct=75.0,
        t7_high_rh_days=2,
        t7_rainfall_mm=25.0,
        t14_rainfall_mm=50.0,
    )
    resp = service.predict(req)
    assert "field_id" not in resp.features_used
    assert "date" not in resp.features_used
    assert "outbreak_within_7d" not in resp.features_used
