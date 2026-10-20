from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def test_fertilizer_schema_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/fertilizer/schema")
        assert response.status_code == 200
        schema = response.json()
        assert "properties" in schema or "required_fields" in schema


def test_fertilizer_model_info_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/fertilizer/model-info")
        assert response.status_code == 200
        info = response.json()
        assert info["model_available"] is True
        assert info["model_version"] == "1.1.0"
        assert "Rice" in info["crops_covered"]


def test_fertilizer_example_endpoint():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/fertilizer/example")
        assert response.status_code == 200
        sample = response.json()
        assert sample["crop"] == "Rice"
        assert sample["state_name"] == "Maharashtra"
        assert "nitrogen__nutrient_index" in sample


def test_fertilizer_recommend_valid_payload():
    with TestClient(create_app()) as client:
        payload = {
            "crop": "Rice",
            "state_name": "Andhra Pradesh",
            "crop_season": "Kharif",
            "nitrogen__nutrient_index": 1.45,
            "phosphorus__nutrient_index": 2.36,
            "potassium__nutrient_index": 1.67,
            "soil_ph__nutrient_index": 2.03,
            "organic_carbon__nutrient_index": 1.80,
        }
        response = client.post("/api/v1/fertilizer/recommend", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["crop"] == "Rice"
        assert body["model_version"] == "1.1.0"
        assert "nitrogen" in body["recommendations"]
        assert body["recommendations"]["nitrogen"]["unit"] == "kg/ha"
        assert "urea_46_pct_n_kg_ha" in body["fertilizer_commercial_equivalent_approx"]
        assert body["fertilizer_commercial_equivalent_approx"]["urea_46_pct_n_kg_ha"] > 0


def test_fertilizer_validation_bounds_rejection():
    with TestClient(create_app()) as client:
        # 1. Out-of-bounds nutrient index (> 3.2)
        invalid_bounds = {
            "crop": "Rice",
            "state_name": "Punjab",
            "nitrogen__nutrient_index": 15.0,
            "phosphorus__nutrient_index": 2.0,
            "potassium__nutrient_index": 2.0,
            "soil_ph__nutrient_index": 2.0,
            "organic_carbon__nutrient_index": 1.8,
        }
        res1 = client.post("/api/v1/fertilizer/recommend", json=invalid_bounds)
        assert res1.status_code == 422

        # 2. Unrecognized crop
        invalid_crop = {
            "crop": "PineappleUnknownCrop",
            "state_name": "Punjab",
            "nitrogen__nutrient_index": 1.5,
            "phosphorus__nutrient_index": 2.0,
            "potassium__nutrient_index": 2.0,
            "soil_ph__nutrient_index": 2.0,
            "organic_carbon__nutrient_index": 1.8,
        }
        res2 = client.post("/api/v1/fertilizer/recommend", json=invalid_crop)
        assert res2.status_code == 422

        # 3. Missing required nutrient index
        missing_index = {
            "crop": "Rice",
            "state_name": "Punjab",
            # missing nitrogen__nutrient_index
            "phosphorus__nutrient_index": 2.0,
            "potassium__nutrient_index": 2.0,
            "soil_ph__nutrient_index": 2.0,
            "organic_carbon__nutrient_index": 1.8,
        }
        res3 = client.post("/api/v1/fertilizer/recommend", json=missing_index)
        assert res3.status_code == 422


def test_fertilizer_service_degraded_when_missing_artifact(tmp_path):
    # App configured with an empty artifact directory where no fertilizer artifact exists
    app = create_app(Settings(artifact_dir=tmp_path))
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["fertilizer_model_available"] is False
        assert health["status"] == "degraded"

        # Attempting recommend returns 503 Service Unavailable without stack traces
        res = client.post(
            "/api/v1/fertilizer/recommend",
            json={
                "crop": "Rice",
                "state_name": "Punjab",
                "nitrogen__nutrient_index": 1.5,
                "phosphorus__nutrient_index": 2.0,
                "potassium__nutrient_index": 2.0,
                "soil_ph__nutrient_index": 2.0,
                "organic_carbon__nutrient_index": 1.8,
            },
        )
        assert res.status_code == 503
        assert "Traceback" not in res.text
