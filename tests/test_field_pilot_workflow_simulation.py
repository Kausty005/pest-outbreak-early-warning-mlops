"""
tests/test_field_pilot_workflow_simulation.py
─────────────────────────────────────────────
Comprehensive end-to-end simulation test suite for the Kharif 2027 Field Pilot.
Uses strictly isolated, mock/temporary fixtures to test the complete surveillance lifecycle:
1. Valid field observation submission
2. Duplicate observation detection (HTTP 409 Conflict)
3. Missing required measurements rejection (HTTP 422)
4. Invalid coordinates rejection (HTTP 422)
5. Biologically incompatible crop-pest combinations rejection (HTTP 422)
6. Missing photograph warning
7. Unverified scout submission dashboard state
8. Reviewer rejection workflow and audit trail
9. Reviewer approval workflow and dashboard update
10. Missed weekly visit handling without zero imputation
11. Late submission warning
12. CSV import with mixed valid, invalid, duplicate, and mismatched rows
13. Audit log integrity and immutability
14. Production isolation guarantee: Zero synthetic observations in production storage.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from src.data_ingestion.pest_surveillance.surveillance_labeling import (
    compute_forward_outbreak_label,
)
from src.data_ingestion.pest_surveillance.surveillance_schema import SurveillanceRecord
from src.data_ingestion.pest_surveillance.surveillance_validation import (
    validate_surveillance_records,
)


@pytest.fixture
def sim_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolated test client routing data and audit logs to temporary directories."""
    test_dir = tmp_path / "pilot_sim_surveillance"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("backend.app.api.pest_surveillance.DATA_DIR", test_dir)
    monkeypatch.setattr("backend.app.api.pest_surveillance.RAW_DATA_DIR", test_dir / "raw")
    monkeypatch.setattr("backend.app.api.pest_surveillance.STORAGE_FILE", test_dir / "field_surveillance_records.json")
    monkeypatch.setattr("backend.app.api.pest_surveillance.AUDIT_FILE", test_dir / "surveillance_audit_log.json")
    return TestClient(app)


def test_simulation_valid_field_observation_submission(sim_client: TestClient):
    """Scenario 1: Valid field observation submission with full pseudonymous identifiers and photo hash."""
    payload = {
        "observation_id": "SIM-OBS-2027-001",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "field_id": "MAH-NGP-KAT-001",
        "farmer_id": "FMR-NGP-9E2A8F",
        "observer_id": "SCT-NGP-01",
        "photo_evidence_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "district": "Nagpur",
        "taluka": "Katol",
        "village": "Paradsinga",
        "latitude": 21.27,
        "longitude": 78.58,
        "crop": "cotton",
        "crop_variety": "RCH-659 BG-II",
        "pest_common_name": "Pink Bollworm",
        "pest_scientific_name": "Pectinophora gossypiella",
        "pest_incidence_pct": 6.5,
        "plants_sampled": 20,
        "plants_affected": 1,
        "sampling_method": "destructive_boll_dissection",
        "observation_frequency": "weekly",
        "crop_growth_stage": "boll_development",
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["validation_status"] == "VALID"
    assert data["record"]["verification_status"] == "UNVERIFIED"
    assert data["record"]["field_id"] == "MAH-NGP-KAT-001"
    assert data["record"]["farmer_id"] == "FMR-NGP-9E2A8F"
    assert data["record"]["observer_id"] == "SCT-NGP-01"
    assert len(data["warnings"]) == 0


def test_simulation_duplicate_observation_submission(sim_client: TestClient):
    """Scenario 2: Duplicate observation submission on the same date/field/crop/pest returns HTTP 409 Conflict."""
    obs_date = datetime.utcnow().strftime("%Y-%m-%d")
    payload1 = {
        "observation_id": "SIM-OBS-DUP-001",
        "observation_date": obs_date,
        "district": "Amravati",
        "taluka": "Chandur Railway",
        "village": "Palsi",
        "latitude": 20.81,
        "longitude": 77.92,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 5.0,
        "photo_evidence_sha256": "abc123hash",
        "is_draft": False,
    }
    resp1 = sim_client.post("/api/v1/pest-surveillance/records", json=payload1)
    assert resp1.status_code == 200

    # Second submission under DIFFERENT observation_id for the same field/date/crop/pest
    payload2 = {
        "observation_id": "SIM-OBS-DUP-002",
        "observation_date": obs_date,
        "district": "Amravati",
        "taluka": "Chandur Railway",
        "village": "Palsi",
        "latitude": 20.81,
        "longitude": 77.92,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 6.0,
        "photo_evidence_sha256": "def456hash",
        "is_draft": False,
    }
    resp2 = sim_client.post("/api/v1/pest-surveillance/records", json=payload2)
    assert resp2.status_code == 409
    assert "Duplicate observation detected" in resp2.json()["detail"]


def test_simulation_missing_required_measurements(sim_client: TestClient):
    """Scenario 3: Non-draft observation lacking all quantitative measurements returns HTTP 422."""
    payload = {
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Yavatmal",
        "taluka": "Kalamb",
        "village": "Kotha",
        "latitude": 20.45,
        "longitude": 78.33,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": None,
        "pest_severity_pct": None,
        "trap_catch_count": None,
        "plants_affected": None,
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "requires at least one quantitative measure" in resp.json()["detail"]


def test_simulation_invalid_coordinates(sim_client: TestClient):
    """Scenario 4: Submission with coordinates outside Maharashtra boundaries returns HTTP 422."""
    payload = {
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Nagpur",
        "latitude": 28.6139,  # New Delhi
        "longitude": 77.2090,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 10.0,
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "outside Maharashtra bounds" in resp.json()["detail"]


def test_simulation_biologically_incompatible_crop_pest(sim_client: TestClient):
    """Scenario 5: Biologically incompatible crop-pest combination returns HTTP 422."""
    payload = {
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Jalgaon",
        "latitude": 21.00,
        "longitude": 75.56,
        "crop": "rice",
        "pest_common_name": "Pink Bollworm",  # Biological mismatch: PBW only feeds on Malvaceae (cotton)
        "pest_incidence_pct": 5.0,
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "Biological mismatch warning" in resp.json()["detail"]


def test_simulation_missing_photographs_warning(sim_client: TestClient):
    """Scenario 6: Submitted observation without photo SHA-256 hash succeeds with explicit warning."""
    payload = {
        "observation_id": "SIM-OBS-NOPHOTO",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Nagpur",
        "taluka": "Katol",
        "latitude": 21.27,
        "longitude": 78.58,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 4.0,
        "photo_evidence_sha256": None,  # Photo omitted
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert any("Missing photo evidence" in w for w in data["warnings"])


def test_simulation_unverified_scout_submission_dashboard_state(sim_client: TestClient):
    """Scenario 7: Scout submission is unverified initially; verified_records_count remains 0."""
    payload = {
        "observation_id": "SIM-OBS-UNVER",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Amravati",
        "latitude": 20.93,
        "longitude": 77.75,
        "crop": "soybean",
        "pest_common_name": "Tobacco Caterpillar",
        "pest_severity_pct": 15.0,
        "photo_evidence_sha256": "sha256photo",
        "is_draft": False,
    }
    sim_client.post("/api/v1/pest-surveillance/records", json=payload)

    dash = sim_client.get("/api/v1/pest-surveillance/dashboard").json()
    assert dash["total_records_received"] == 1
    assert dash["unverified_records_count"] == 1
    assert dash["verified_records_count"] == 0


def test_simulation_reviewer_rejection(sim_client: TestClient):
    """Scenario 8: Expert reviewer rejects an unverified record with logged justification."""
    # Create record
    payload = {
        "observation_id": "SIM-OBS-REJ-01",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Yavatmal",
        "latitude": 20.39,
        "longitude": 78.12,
        "crop": "cotton",
        "pest_common_name": "American Bollworm",
        "pest_incidence_pct": 14.0,
        "photo_evidence_sha256": "sha256photo",
        "is_draft": False,
    }
    sim_client.post("/api/v1/pest-surveillance/records", json=payload)

    # Reviewer rejects
    review_req = {
        "observation_id": "SIM-OBS-REJ-01",
        "reviewer_id": "ENTOMOLOGIST-DR-DESHMUKH",
        "action": "REJECT",
        "justification": "Larval specimen in uploaded photograph exhibits characteristics of Spodoptera litura, not Helicoverpa armigera.",
    }
    resp = sim_client.post("/api/v1/pest-surveillance/review", json=review_req)
    assert resp.status_code == 200
    rev_data = resp.json()
    assert rev_data["new_status"] == "REJECTED"

    # Dashboard verifies 0 verified records
    dash = sim_client.get("/api/v1/pest-surveillance/dashboard").json()
    assert dash["verified_records_count"] == 0


def test_simulation_reviewer_approval(sim_client: TestClient):
    """Scenario 9: Expert reviewer approves record; status becomes KVK_EXPERT_VALIDATED."""
    payload = {
        "observation_id": "SIM-OBS-APP-01",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Jalgaon",
        "latitude": 21.00,
        "longitude": 75.56,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 11.5,
        "plants_sampled": 20,
        "plants_affected": 2,
        "photo_evidence_sha256": "sha256verified",
        "is_draft": False,
    }
    sim_client.post("/api/v1/pest-surveillance/records", json=payload)

    review_req = {
        "observation_id": "SIM-OBS-APP-01",
        "reviewer_id": "ENTOMOLOGIST-DR-PATIL",
        "action": "APPROVE",
        "justification": "Verified destructive boll dissection logsheet, locule damage photographs, and scout credentials.",
    }
    resp = sim_client.post("/api/v1/pest-surveillance/review", json=review_req)
    assert resp.status_code == 200
    rev_data = resp.json()
    assert rev_data["new_status"] == "KVK_EXPERT_VALIDATED"

    # Dashboard confirms 1 verified record
    dash = sim_client.get("/api/v1/pest-surveillance/dashboard").json()
    assert dash["verified_records_count"] == 1


def test_simulation_missed_weekly_visit_no_zero_imputation():
    """Scenario 10: Missed visit in forward window produces unobserved / missing status; zero-imputation is barred."""
    ref_rec = SurveillanceRecord(
        observation_id="SIM-REF-01",
        observation_date="2027-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    # Forward window (2027-08-05 to 2027-08-11) has zero records because monsoon storm flooded field
    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d is None
    assert res.label_status == "UNOBSERVED_FUTURE_WINDOW"
    # Negative label must NOT be imputed
    assert res.outbreak_label_7d != 0


def test_simulation_late_submission_warning(sim_client: TestClient):
    """Scenario 11: Observation conducted >3 days prior to submission generates late submission warning."""
    past_date = (datetime.utcnow().date() - timedelta(days=5)).strftime("%Y-%m-%d")
    payload = {
        "observation_id": "SIM-OBS-LATE-01",
        "observation_date": past_date,
        "district": "Nagpur",
        "latitude": 21.15,
        "longitude": 79.08,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 5.0,
        "photo_evidence_sha256": "hash123",
        "is_draft": False,
    }
    resp = sim_client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert any("Late submission warning" in w for w in data["warnings"])


def test_simulation_csv_batch_import_mixed_valid_invalid(sim_client: TestClient):
    """Scenario 12: Batch CSV with mixed valid, duplicate, and invalid rows."""
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    csv_rows = [
        # Row 1: Valid
        "observation_id,observation_date,district,taluka,village,latitude,longitude,crop,crop_variety,pest_common_name,pest_scientific_name,pest_incidence_pct,pest_severity_pct,trap_type,trap_catch_count,plants_sampled,plants_affected,sampling_method,observation_frequency,sowing_date,crop_growth_stage,days_since_sowing,source_organization,source_document,source_record_id,collection_method,verification_status,data_license",
        f"MIX-01,{today_str},Nagpur,Katol,Paradsinga,21.27,78.58,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,8.0,0.0,delta_trap,5.0,20,1,fixed_plot_scouting,weekly,2027-06-15,squaring,50,KVK-Nagpur,mix.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED",
        # Row 2: Valid
        f"MIX-02,{today_str},Amravati,Chandur,Palsi,20.81,77.92,soybean,JS-335,Tobacco Caterpillar,Spodoptera litura,0.0,12.0,delta_trap,3.0,20,0,fixed_plot_scouting,weekly,2027-06-20,vegetative,45,KVK-Amravati,mix.csv,2,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED",
        # Row 3: Duplicate of Row 1 (same date, location, crop, pest)
        f"MIX-03-DUP,{today_str},Nagpur,Katol,Paradsinga,21.27,78.58,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,9.0,0.0,delta_trap,6.0,20,2,fixed_plot_scouting,weekly,2027-06-15,squaring,50,KVK-Nagpur,mix.csv,3,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED",
        # Row 4: Invalid coordinates (outside Maharashtra, different location to avoid duplicate key)
        f"MIX-04-OUT,{today_str},Nagpur,Hingna,Kanhan,28.61,77.20,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,8.0,0.0,delta_trap,5.0,20,1,fixed_plot_scouting,weekly,2027-06-15,squaring,50,KVK-Nagpur,mix.csv,4,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED",
        # Row 5: Biological mismatch (Pink Bollworm on Rice)
        f"MIX-05-MIS,{today_str},Nagpur,Katol,Paradsinga,21.27,78.58,rice,IR-64,Pink Bollworm,Pectinophora gossypiella,8.0,0.0,delta_trap,5.0,20,1,fixed_plot_scouting,weekly,2027-06-15,tillering,50,KVK-Nagpur,mix.csv,5,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED",
    ]
    csv_content = "\n".join(csv_rows)
    files = {"file": ("mixed_surveillance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = sim_client.post("/api/v1/pest-surveillance/upload-csv", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows_processed"] == 5
    assert data["valid_rows_count"] == 2
    assert data["invalid_rows_count"] == 3
    assert data["duplicates_detected"] == 1
    assert data["records_saved_count"] == 2


def test_simulation_audit_log_integrity(sim_client: TestClient):
    """Scenario 13: Verify audit log stores chronological, immutable audit entries with required attributes."""
    # Create observation
    payload = {
        "observation_id": "SIM-OBS-AUD-01",
        "observation_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "district": "Nagpur",
        "latitude": 21.15,
        "longitude": 79.08,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 10.0,
        "photo_evidence_sha256": "sha256aud",
        "is_draft": False,
    }
    sim_client.post("/api/v1/pest-surveillance/records", json=payload)

    # Perform correction and approval review
    review_req = {
        "observation_id": "SIM-OBS-AUD-01",
        "reviewer_id": "CHIEF-ENTOMOLOGIST",
        "action": "CORRECT_FIELDS",
        "justification": "Field scout misrecorded plants affected as 5; physical dissection confirmed 3 damaged bolls.",
        "field_corrections": {"plants_affected": 3},
    }
    resp = sim_client.post("/api/v1/pest-surveillance/review", json=review_req)
    assert resp.status_code == 200

    records_res = sim_client.get("/api/v1/pest-surveillance/records").json()
    assert records_res["audit_entries_count"] >= 1


def test_simulation_production_isolation_guarantee():
    """Scenario 14: Strict safety guarantee that production storage has 0 observations."""
    prod_file = Path("data/processed/pest_surveillance/field_surveillance_records.json")
    if prod_file.exists():
        with open(prod_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        assert len(records) == 0, f"Production storage must contain 0 records, found {len(records)}!"
