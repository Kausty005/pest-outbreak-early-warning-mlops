"""
tests/test_api_pest_risk.py
───────────────────────────
Integration tests for the experimental pest risk assessment FastAPI endpoints:
- POST /api/v1/pest-risk/environmental-assessment
- GET  /api/v1/pest-risk/supported-profiles

Verifies:
- Accurate biophysical favorability evaluation
- Unsupported crop/pest/district error handling
- Graceful handling of missing edaphic or forecast data
- Absolute absence of misleading 'outbreak_probability' claims
- Compliance with the experimental early-warning protocol
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# 1. SUPPORTED PROFILES DISCOVERY TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_get_supported_profiles(client: TestClient):
    response = client.get("/api/v1/pest-risk/supported-profiles")
    assert response.status_code == 200
    data = response.json()

    assert "supported_crops" in data
    assert set(data["supported_crops"]) == {"cotton", "soybean", "rice", "maize"}

    assert "crop_pests_mapping" in data
    assert "cotton" in data["crop_pests_mapping"]
    cotton_pests = [p["common_name"] for p in data["crop_pests_mapping"]["cotton"]]
    assert "Pink Bollworm" in cotton_pests

    assert "available_surveillance_districts" in data
    assert "Nagpur" in data["available_surveillance_districts"]
    assert "Amravati" in data["available_surveillance_districts"]

    assert "available_date_range" in data
    assert data["available_date_range"]["start"] == "2023-06-01"
    assert data["available_date_range"]["end"] == "2023-10-31"


# ══════════════════════════════════════════════════════════════════════════════
# 2. SUCCESSFUL ENVIRONMENTAL ASSESSMENT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_successful_environmental_assessment_cotton_nagpur(client: TestClient):
    payload = {
        "crop": "cotton",
        "district": "Nagpur",
        "pest": "pink_bollworm",
        "assessment_date": "2023-09-15",
        "planting_date": "2023-06-15",
        "fetch_live_forecast": False,
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Required label & type
    assert data["assessment_type"] == "EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT"
    assert data["crop"] == "cotton"
    assert data["pest"] == "Pink Bollworm"
    assert data["scientific_name"] == "Pectinophora gossypiella (Saunders)"
    assert data["location"] == "Nagpur"
    assert data["assessment_date"] == "2023-09-15"

    # Score in bounded [0.0, 1.0]
    score = data["environmental_favorability_score"]
    assert 0.0 <= score <= 1.0
    assert data["risk_category"] in {"LOW", "MODERATE", "HIGH"}
    assert data["risk_trend"] in {"RISING", "STABLE", "DECLINING", "UNKNOWN"}

    # Contributing factors
    factors = data["contributing_factors"]
    assert "favorable_drivers" in factors
    assert "limiting_factors" in factors

    # Observations
    obs = data["environmental_observations"]
    assert obs["temperature_mean_c"] > 0
    assert obs["relative_humidity_pct"] > 0
    assert obs["antecedent_window_days"] == 7

    # Data quality
    dq = data["data_quality"]
    assert dq["records_used"] == 7
    assert dq["edaphic_data_available"] is True
    assert dq["phenology_data_available"] is True

    # Actionable IPM & biological citations
    assert len(data["recommendations"]) >= 2
    assert len(data["limitations"]) >= 3
    assert len(data["references"]) >= 2
    for ref in data["references"]:
        assert "title" in ref
        assert "url" in ref

    # Absolute safety check: NO outbreak_probability
    assert "outbreak_probability" not in data


def test_successful_assessment_default_latest_date_and_default_pest(client: TestClient):
    payload = {
        "crop": "soybean",
        "district": "Amravati",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["crop"] == "soybean"
    assert data["pest"] == "Tobacco Caterpillar"
    assert data["assessment_date"] == "2023-10-31"
    assert data["data_quality"]["phenology_data_available"] is False
    assert any("Sowing date was not specified" in notice for notice in data["data_quality"]["data_notices"])


# ══════════════════════════════════════════════════════════════════════════════
# 3. UNSUPPORTED CROPS, PESTS & DISTRICTS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_unsupported_crop_rejected(client: TestClient):
    payload = {
        "crop": "sugarcane",
        "district": "Nagpur",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Unsupported crop 'sugarcane'" in detail
    assert "cotton" in detail


def test_unsupported_pest_for_crop_rejected(client: TestClient):
    payload = {
        "crop": "cotton",
        "district": "Nagpur",
        "pest": "desert_locust",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Unsupported pest 'desert_locust'" in detail
    assert "pink_bollworm" in detail


def test_unsupported_district_rejected(client: TestClient):
    payload = {
        "crop": "cotton",
        "district": "Nashik",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Surveillance data for district 'Nashik' is not yet available" in detail
    assert "Nagpur" in detail


def test_date_preceding_available_records_rejected(client: TestClient):
    payload = {
        "crop": "cotton",
        "district": "Nagpur",
        "assessment_date": "2022-01-01",  # Precedes June 2023
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "precedes earliest available record" in detail


# ══════════════════════════════════════════════════════════════════════════════
# 4. INPUT VALIDATION & SAFETY PROTOCOL TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_invalid_input_schema(client: TestClient):
    # Missing required 'district' field
    payload = {
        "crop": "cotton",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 422


def test_response_never_contains_outbreak_probability(client: TestClient):
    payload = {
        "crop": "maize",
        "district": "Jalgaon",
        "assessment_date": "2023-08-20",
    }
    response = client.post("/api/v1/pest-risk/environmental-assessment", json=payload)
    assert response.status_code == 200
    body = response.text
    # Ensure raw string does not contain outbreak_probability as a key
    assert '"outbreak_probability"' not in body

