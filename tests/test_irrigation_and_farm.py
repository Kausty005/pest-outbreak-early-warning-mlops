from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.ml.irrigation import assess_irrigation_need, CROP_MOISTURE_PROFILES


def test_irrigation_rules_optimal_and_deficit():
    # Rice optimal is 70-85%
    adv_opt = assess_irrigation_need("rice", current_soil_moisture=75.0, current_temp_c=28.0)
    assert adv_opt["status"] == "OPTIMAL"
    assert adv_opt["moisture_deficit_pct"] == 0.0
    assert adv_opt["water_volume_liters"] == 0

    # Rice with severe moisture deficit (40% < critical 55%)
    adv_crit = assess_irrigation_need("rice", current_soil_moisture=40.0, current_temp_c=34.0, zone_area_acres=2.5)
    assert adv_crit["status"] == "CRITICAL_DEFICIT"
    assert adv_crit["moisture_deficit_pct"] > 0
    assert adv_crit["water_volume_liters"] > 0
    assert adv_crit["estimated_pump_runtime_hours"] > 0
    assert "Shallow flooding" in adv_crit["recommended_method"]

    # Chickpea (drought-tolerant pulse, optimal 35-50%)
    adv_pulse = assess_irrigation_need("chickpea", current_soil_moisture=42.0)
    assert adv_pulse["status"] == "OPTIMAL"

    # Waterlogged test (soil moisture 96%)
    adv_waterlog = assess_irrigation_need("chickpea", current_soil_moisture=96.0)
    assert adv_waterlog["status"] == "WATERLOGGED"
    assert "Drainage" in adv_waterlog["urgency"]


def test_farm_zones_api(tmp_path):
    app = create_app(Settings(artifact_dir=tmp_path))
    with TestClient(app) as client:
        # 1. List all 5 zones
        res = client.get("/api/v1/farm/zones")
        assert res.status_code == 200
        zones = res.json()
        assert len(zones) == 5
        zone_ids = [z["id"] for z in zones]
        assert "zone-1" in zone_ids
        assert "zone-5" in zone_ids

        # 2. Get single zone
        res = client.get("/api/v1/farm/zones/zone-1")
        assert res.status_code == 200
        z1 = res.json()
        assert z1["active_crop"] == "rice"
        assert "irrigation_summary" in z1

        # 3. Telemetry ingestion from hardware IoT
        payload = {
            "N": 85.0,
            "P": 48.0,
            "K": 40.0,
            "temperature": 29.5,
            "humidity": 78.0,
            "ph": 6.3,
            "rainfall": 15.0,
            "soil_moisture": 62.0,
        }
        res = client.post("/api/v1/farm/zones/zone-1/telemetry", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # 4. Simulation trigger
        res = client.post("/api/v1/farm/zones/zone-2/simulate?scenario=dry_spell")
        assert res.status_code == 200
        assert res.json()["status"] == "simulated"

        # 5. 360° Zone Advisory endpoint
        res = client.get("/api/v1/farm/zones/zone-1/advisory")
        assert res.status_code == 200
        data = res.json()
        assert "journey_guidance" in data
        guidance = data["journey_guidance"]
        assert "irrigation" in guidance
        assert "crop_suitability" in guidance
        assert "pest_protection" in guidance
        assert guidance["irrigation"]["status"] in {"OPTIMAL", "MODERATE_DEFICIT", "CRITICAL_DEFICIT", "WATERLOGGED", "ADEQUATE_HIGH"}

        # 6. Agro-weather endpoint
        res = client.get("/api/v1/farm/weather")
        assert res.status_code == 200
        w = res.json()
        assert "temperature_c" in w
        assert "humidity_pct" in w
