"""
tests/test_api_pest_surveillance.py
───────────────────────────────────
Test suite for the Field Pest Surveillance API endpoints:
- Dashboard metrics (zero counts when empty)
- Single observation recording and biological/geographic validation
- Batch CSV upload and validation reporting
- Human review workflow and audit logging
- Scientific invariants enforcement
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Route storage to a temporary directory for isolation
    test_dir = tmp_path / "pest_surveillance"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("backend.app.api.pest_surveillance.DATA_DIR", test_dir)
    monkeypatch.setattr("backend.app.api.pest_surveillance.RAW_DATA_DIR", test_dir / "raw")
    monkeypatch.setattr("backend.app.api.pest_surveillance.STORAGE_FILE", test_dir / "field_surveillance_records.json")
    monkeypatch.setattr("backend.app.api.pest_surveillance.AUDIT_FILE", test_dir / "surveillance_audit_log.json")
    return TestClient(app)


def test_surveillance_dashboard_initial_zero_metrics(client: TestClient):
    """Dashboard must show 0 for counts when no authentic data exists (never simulated)."""
    resp = client.get("/api/v1/pest-surveillance/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records_received"] == 0
    assert data["unique_fields_monitored"] == 0
    assert data["verified_records_count"] == 0
    assert data["unverified_records_count"] == 0
    assert data["draft_records_count"] == 0
    assert data["positive_outbreak_windows"] == 0
    assert data["verified_negative_windows"] == 0
    assert data["scientific_invariants"]["ml_training_allowed"] is False
    assert data["scientific_invariants"]["supervised_outbreak_model_status"] == "BLOCKED"
    assert "CROPSAP-Maharashtra" in data["institutional_access_status"]
    assert "ICAR-CICR-Nagpur" in data["institutional_access_status"]


def test_create_valid_surveillance_observation(client: TestClient):
    """Test entering a valid single observation (defaults to UNVERIFIED)."""
    payload = {
        "observation_date": "2026-10-15",
        "district": "Nagpur",
        "taluka": "Hingna",
        "village": "Adegaon",
        "latitude": 21.05,
        "longitude": 78.95,
        "crop": "cotton",
        "crop_variety": "RCH-659 BG-II",
        "pest_common_name": "Pink Bollworm",
        "pest_scientific_name": "Pectinophora gossypiella",
        "pest_incidence_pct": 12.5,
        "plants_sampled": 20,
        "plants_affected": 3,
        "sampling_method": "destructive_boll_dissection",
        "observation_frequency": "weekly",
        "sowing_date": "2026-06-20",
        "crop_growth_stage": "Boll Development",
        "observer_id": "SCOUT-NAG-01",
        "is_draft": False,
    }
    resp = client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["validation_status"] == "VALID"
    assert data["record"]["verification_status"] == "UNVERIFIED"
    assert data["record"]["district"] == "Nagpur"
    assert data["record"]["pest_incidence_pct"] == 12.5


def test_create_draft_surveillance_observation(client: TestClient):
    """Draft observations can have partial fields and receive DRAFT status."""
    payload = {
        "observation_date": "2026-10-16",
        "district": "Amravati",
        "latitude": 20.93,
        "longitude": 77.75,
        "crop": "soybean",
        "pest_common_name": "Tobacco Caterpillar",
        "is_draft": True,
    }
    resp = client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["validation_status"] == "DRAFT"
    assert data["record"]["verification_status"] == "DRAFT"


def test_reject_biological_mismatch_in_submitted_record(client: TestClient):
    """Biological mismatch (e.g. Pink Bollworm on Rice) must be rejected for submitted records."""
    payload = {
        "observation_date": "2026-10-15",
        "district": "Nagpur",
        "latitude": 21.05,
        "longitude": 78.95,
        "crop": "rice",
        "pest_common_name": "Pink Bollworm",  # Mismatch: PBW only affects cotton
        "pest_incidence_pct": 15.0,
        "is_draft": False,
    }
    resp = client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "Biological mismatch warning" in resp.json()["detail"]


def test_reject_out_of_bounds_coordinates(client: TestClient):
    """Coordinates outside Maharashtra must be rejected."""
    payload = {
        "observation_date": "2026-10-15",
        "district": "Nagpur",
        "latitude": 12.97,  # Bengaluru latitude, outside Maharashtra
        "longitude": 77.59,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 5.0,
        "is_draft": False,
    }
    resp = client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "outside Maharashtra bounds" in resp.json()["detail"]


def test_batch_csv_upload_and_validation(client: TestClient):
    """Test uploading a batch CSV and receiving structural validation report."""
    csv_content = (
        "observation_id,observation_date,district,taluka,village,latitude,longitude,crop,crop_variety,pest_common_name,pest_scientific_name,pest_incidence_pct,pest_severity_pct,trap_type,trap_catch_count,plants_sampled,plants_affected,sampling_method,observation_frequency,sowing_date,crop_growth_stage,days_since_sowing,source_organization,source_document,source_record_id,collection_method,verification_status,data_license\n"
        "OBS-2026-001,2026-08-10,Nagpur,Hingna,Adegaon,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,8.5,5.0,delta_trap,6.0,20,2,fixed_plot_scouting,weekly,2026-06-15,Squaring,56,KVK-Nagpur,test.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
        "OBS-2026-002,2026-08-17,Nagpur,Hingna,Adegaon,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,12.0,8.0,delta_trap,9.0,20,3,fixed_plot_scouting,weekly,2026-06-15,Flowering,63,KVK-Nagpur,test.csv,2,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
    )
    files = {"file": ("surveillance_batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/pest-surveillance/upload-csv", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["total_rows_processed"] == 2
    assert data["valid_rows_count"] == 2
    assert data["invalid_rows_count"] == 0
    assert len(data["file_sha256"]) == 64

    # Verify dashboard now reflects uploaded records
    dash = client.get("/api/v1/pest-surveillance/dashboard").json()
    assert dash["total_records_received"] == 2
    assert dash["unverified_records_count"] == 2


def test_human_review_workflow_and_audit_logging(client: TestClient):
    """Test approving a record and verifying audit trail."""
    # First create an observation
    payload = {
        "observation_id": "OBS-REV-001",
        "observation_date": "2026-09-01",
        "district": "Yavatmal",
        "taluka": "Darwha",
        "village": "Lohara",
        "latitude": 20.32,
        "longitude": 77.76,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 7.0,
        "plants_sampled": 20,
        "plants_affected": 2,
        "is_draft": False,
    }
    client.post("/api/v1/pest-surveillance/records", json=payload)

    # Reviewer approves the record
    review_payload = {
        "observation_id": "OBS-REV-001",
        "reviewer_id": "ENTOMOLOGIST-DR-SHARMA",
        "action": "APPROVE",
        "justification": "Checked scouting methodology and boll dissection notes; confirmed sub-ETL incidence.",
    }
    resp = client.post("/api/v1/pest-surveillance/review", json=review_payload)
    assert resp.status_code == 200
    rev_data = resp.json()
    assert rev_data["success"] is True
    assert rev_data["new_status"] == "KVK_EXPERT_VALIDATED"
    assert rev_data["reviewed_by"] == "ENTOMOLOGIST-DR-SHARMA"
    assert rev_data["audit_id"].startswith("AUD-")

    # Verify dashboard updated
    dash = client.get("/api/v1/pest-surveillance/dashboard").json()
    assert dash["verified_records_count"] == 1


def test_human_review_rejection_and_corrections(client: TestClient):
    """Test rejecting an invalid record and applying corrections with audit trail."""
    # 1. Create record to reject
    payload1 = {
        "observation_id": "OBS-REJ-001",
        "observation_date": "2026-09-02",
        "district": "Jalgaon",
        "latitude": 20.99,
        "longitude": 75.56,
        "crop": "maize",
        "pest_common_name": "Fall Armyworm",
        "pest_incidence_pct": 25.0,
        "plants_sampled": 100,
        "plants_affected": 25,
        "is_draft": False,
    }
    client.post("/api/v1/pest-surveillance/records", json=payload1)

    # Reject
    rej_payload = {
        "observation_id": "OBS-REJ-001",
        "reviewer_id": "ENTOMOLOGIST-DR-PATIL",
        "action": "REJECT",
        "justification": "Photo evidence shows grasshopper damage rather than Fall Armyworm whorl feeding.",
    }
    resp1 = client.post("/api/v1/pest-surveillance/review", json=rej_payload)
    assert resp1.status_code == 200
    assert resp1.json()["new_status"] == "REJECTED"

    # 2. Create record to correct
    payload2 = {
        "observation_id": "OBS-CORR-001",
        "observation_date": "2026-09-03",
        "district": "Amravati",
        "latitude": 20.93,
        "longitude": 77.75,
        "crop": "soybean",
        "pest_common_name": "Tobacco Caterpillar",
        "pest_incidence_pct": 14.0,
        "plants_sampled": 20,
        "plants_affected": 3,
        "is_draft": False,
    }
    client.post("/api/v1/pest-surveillance/records", json=payload2)

    # Correct field
    corr_payload = {
        "observation_id": "OBS-CORR-001",
        "reviewer_id": "ENTOMOLOGIST-DR-PATIL",
        "action": "CORRECT_FIELDS",
        "justification": "Field scout miscounted sampled plants; corrected from 20 to 25 based on field sheet.",
        "field_corrections": {"plants_sampled": 25, "pest_incidence_pct": 12.0},
    }
    resp2 = client.post("/api/v1/pest-surveillance/review", json=corr_payload)
    assert resp2.status_code == 200
    assert resp2.json()["new_status"] == "FIELD_SCOUT_VERIFIED"

    # Verify updated record
    records = client.get("/api/v1/pest-surveillance/records").json()["records"]
    target = next(r for r in records if r["observation_id"] == "OBS-CORR-001")
    assert target["plants_sampled"] == 25
    assert target["pest_incidence_pct"] == 12.0


def test_missing_mandatory_measurement_rejected(client: TestClient):
    """Submitted non-draft record without any quantitative measure must be rejected."""
    payload = {
        "observation_date": "2026-09-04",
        "district": "Nagpur",
        "latitude": 21.05,
        "longitude": 78.95,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        # No incidence, severity, trap catch, or plants affected provided!
        "is_draft": False,
    }
    resp = client.post("/api/v1/pest-surveillance/records", json=payload)
    assert resp.status_code == 422
    assert "requires at least one quantitative measure" in resp.json()["detail"]


def test_csv_upload_duplicate_detection(client: TestClient):
    """Batch CSV upload must detect and report duplicate rows."""
    duplicate_csv = (
        "observation_id,observation_date,district,taluka,village,latitude,longitude,crop,crop_variety,pest_common_name,pest_scientific_name,pest_incidence_pct,pest_severity_pct,trap_type,trap_catch_count,plants_sampled,plants_affected,sampling_method,observation_frequency,sowing_date,crop_growth_stage,days_since_sowing,source_organization,source_document,source_record_id,collection_method,verification_status,data_license\n"
        "OBS-DUP-01,2026-08-10,Nagpur,Hingna,Adegaon,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,8.5,5.0,delta_trap,6.0,20,2,fixed_plot_scouting,weekly,2026-06-15,Squaring,56,KVK-Nagpur,test.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
        "OBS-DUP-01,2026-08-10,Nagpur,Hingna,Adegaon,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,8.5,5.0,delta_trap,6.0,20,2,fixed_plot_scouting,weekly,2026-06-15,Squaring,56,KVK-Nagpur,test.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
    )
    files = {"file": ("duplicates.csv", io.BytesIO(duplicate_csv.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/pest-surveillance/upload-csv", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["duplicates_detected"] == 1
    assert data["valid_rows_count"] == 1


