from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_unified_advisory_pipeline():
    with TestClient(create_app()) as client:
        payload = {
            "N": 80.0,
            "P": 40.0,
            "K": 40.0,
            "temperature": 26.0,
            "humidity": 80.0,
            "ph": 6.5,
            "rainfall": 200.0,
            "state_name": "Maharashtra",
        }
        response = client.post("/api/v1/advisory/unified", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "crop_recommendation" in data
        assert "primary_crop" in data["crop_recommendation"]
        assert len(data["crop_recommendation"]["top_candidates"]) > 0

        assert "fertilizer_advisory" in data
        assert data["fertilizer_advisory"] is not None
        assert "recommendations" in data["fertilizer_advisory"]

        assert "pest_early_warning_preview" in data
        pest = data["pest_early_warning_preview"]
        assert "primary_threat" in pest
        assert "preliminary_risk_level" in pest
        assert "next_phase_note" in pest

        assert "field_guidance" in data
        assert len(data["field_guidance"]) > 0


def test_unified_advisory_cotton_pest_risk_scenario():
    with TestClient(create_app()) as client:
        # High temperature & humidity for cotton pest risk trigger
        payload = {
            "N": 120.0,
            "P": 50.0,
            "K": 50.0,
            "temperature": 31.0,
            "humidity": 78.0,
            "ph": 7.0,
            "rainfall": 80.0,
            "state_name": "Maharashtra",
            "target_crop_override": "Cotton",
        }
        response = client.post("/api/v1/advisory/unified", json=payload)
        assert response.status_code == 200
        data = response.json()

        pest = data["pest_early_warning_preview"]
        assert "Bollworm" in pest["primary_threat"]
        assert pest["preliminary_risk_level"] == "HIGH"
