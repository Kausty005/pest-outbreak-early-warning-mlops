"""
tests/test_crop_catalog.py
──────────────────────────
Unit and integration tests for the Centralized Crop Catalog,
canonical mapping, and Pest Outbreak Early-Warning preliminary interfaces.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.crop_catalog import get_crop_catalog
from backend.app.main import create_app
from backend.app.schemas.fertilizer import normalize_crop_name


def test_crop_catalog_loading_and_counts():
    catalog = get_crop_catalog()
    all_crops = catalog.list_all_crops()
    assert len(all_crops) == 24

    # Verify model coverage counts match metadata
    crop_pred_supported = catalog.list_supported_crops("crop_prediction")
    fert_supported = catalog.list_supported_crops("fertilizer_recommendation")
    pest_preview_supported = catalog.list_supported_crops("pest_outbreak_preview")
    pest_ml_eligible = catalog.list_pest_eligible_crops()

    assert len(crop_pred_supported) == 22
    assert len(fert_supported) == 4  # Rice, Maize, Wheat, Sugarcane (canonical base crops)
    assert len(pest_preview_supported) == 3  # Cotton, Rice, Maize
    assert len(pest_ml_eligible) == 7  # Tier 1 & Tier 2 eligible crops


def test_canonical_id_resolution_and_aliases():
    catalog = get_crop_catalog()

    # Direct canonical IDs
    assert catalog.resolve_canonical_id("cotton") == "cotton"
    assert catalog.resolve_canonical_id("rice") == "rice"
    assert catalog.resolve_canonical_id("maize") == "maize"

    # Common aliases & synonyms
    assert catalog.resolve_canonical_id("corn") == "maize"
    assert catalog.resolve_canonical_id("paddy") == "rice"
    assert catalog.resolve_canonical_id("dhan") == "rice"
    assert catalog.resolve_canonical_id("kapas") == "cotton"
    assert catalog.resolve_canonical_id("gehun") == "wheat"
    assert catalog.resolve_canonical_id("ganna") == "sugarcane"
    assert catalog.resolve_canonical_id("chana") == "chickpea"
    assert catalog.resolve_canonical_id("tur") == "pigeonpeas"

    # Case insensitivity & whitespace tolerance
    assert catalog.resolve_canonical_id("  COTTON  ") == "cotton"
    assert catalog.resolve_canonical_id("Kharif Rice") == "rice"
    assert catalog.resolve_canonical_id("Rabi Maize") == "maize"


def test_fertilizer_identifier_resolution():
    catalog = get_crop_catalog()

    # Supported crops
    assert catalog.get_fertilizer_identifier("rice") == "Rice"
    assert catalog.get_fertilizer_identifier("paddy") == "Rice"
    assert catalog.get_fertilizer_identifier("wheat") == "Wheat"
    assert catalog.get_fertilizer_identifier("sugarcane") == "Sugarcane"
    assert catalog.get_fertilizer_identifier("maize") == "Kharif Maize"
    assert catalog.get_fertilizer_identifier("maize", season="Rabi") == "Rabi Maize"

    # Unsupported crops fallback gracefully to Rice default baseline
    assert catalog.get_fertilizer_identifier("cotton") == "Rice"
    assert catalog.get_fertilizer_identifier("apple") == "Rice"


def test_normalize_crop_name_backward_compatibility():
    # Existing behavior preserved
    assert normalize_crop_name("Rice") == "Rice"
    assert normalize_crop_name("rice") == "Rice"
    assert normalize_crop_name("Wheat") == "Wheat"
    assert normalize_crop_name("Sugarcane") == "Sugarcane"
    assert normalize_crop_name("Kharif Maize") == "Kharif Maize"
    assert normalize_crop_name("Rabi Maize") == "Rabi Maize"
    assert normalize_crop_name("corn") == "Kharif Maize"
    assert normalize_crop_name("paddy") == "Rice"


def test_pest_outbreak_specifications():
    catalog = get_crop_catalog()

    # Cotton specification
    cotton_spec = catalog.get_pest_specification("cotton")
    assert cotton_spec is not None
    assert cotton_spec["canonical_id"] == "cotton"
    pred_spec = cotton_spec["pest_outbreak_prediction"]
    assert pred_spec["eligible"] is True
    assert pred_spec["priority_tier"] == "TIER_1_PRIMARY"
    assert any("Pink Bollworm" in p["common_name"] for p in pred_spec["target_pests"])
    assert len(pred_spec["historical_data_requirements"]) > 0
    assert len(pred_spec["weather_feature_requirements"]) > 0

    # Rice specification
    rice_spec = catalog.get_pest_specification("rice")
    assert rice_spec is not None
    assert any("Stem Borer" in p["common_name"] for p in rice_spec["pest_outbreak_prediction"]["target_pests"])

    # Ineligible crop
    apple_spec = catalog.get_pest_specification("apple")
    assert apple_spec["pest_outbreak_prediction"]["eligible"] is False


def test_crop_catalog_api_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/crop/catalog")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "crops" in data
        assert len(data["crops"]) == 24
        canonical_ids = [c["canonical_id"] for c in data["crops"]]
        assert "cotton" in canonical_ids
        assert "rice" in canonical_ids
        assert "maize" in canonical_ids
        assert "wheat" in canonical_ids
        assert "sugarcane" in canonical_ids


def test_pest_eligible_crops_api_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/pest/eligible-crops")
        assert response.status_code == 200
        crops = response.json()
        assert len(crops) >= 3
        crop_ids = [c["canonical_id"] for c in crops]
        assert "cotton" in crop_ids
        assert "rice" in crop_ids
        assert "maize" in crop_ids


def test_pest_spec_endpoint():
    with TestClient(create_app()) as client:
        # Valid cotton spec
        res = client.get("/api/v1/pest/spec/cotton")
        assert res.status_code == 200
        spec = res.json()
        assert spec["canonical_id"] == "cotton"
        assert spec["priority_tier"] == "TIER_1_PRIMARY"
        assert len(spec["target_pests"]) > 0

        # Alias resolution works
        res_alias = client.get("/api/v1/pest/spec/corn")
        assert res_alias.status_code == 200
        assert res_alias.json()["canonical_id"] == "maize"

        # Ineligible crop returns 400
        res_ineligible = client.get("/api/v1/pest/spec/apple")
        assert res_ineligible.status_code == 400

        # Non-existent crop returns 404
        res_404 = client.get("/api/v1/pest/spec/non_existent_crop_xyz")
        assert res_404.status_code == 404


def test_pest_preview_api_endpoint():
    with TestClient(create_app()) as client:
        payload = {
            "crop": "kapas",  # Cotton alias
            "temperature": 30.0,
            "humidity": 75.0,
            "rainfall": 50.0,
            "state_name": "Maharashtra",
        }
        res = client.post("/api/v1/pest/preview", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["crop_canonical_id"] == "cotton"
        assert "Bollworm" in data["primary_threat"]
        assert data["preliminary_risk_level"] == "HIGH"
        assert len(data["target_pests"]) > 0
