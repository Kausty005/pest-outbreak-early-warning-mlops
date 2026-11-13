"""
tests/test_api_public_advisories.py
───────────────────────────────────
Test suite for Public Pest Advisory & Intelligence FastAPI endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_get_public_advisories_list():
    resp = client.get("/api/v1/public-advisories")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_count" in data
    assert "filtered_count" in data
    assert "advisories" in data
    assert "disclaimer" in data
    assert "NOT verified field-level surveillance" in data["disclaimer"]
    assert len(data["advisories"]) > 0


def test_filter_advisories_by_crop():
    resp = client.get("/api/v1/public-advisories?crop=cotton")
    assert resp.status_code == 200
    data = resp.json()
    for adv in data["advisories"]:
        assert adv["crop"] == "cotton"


def test_filter_advisories_by_district():
    resp = client.get("/api/v1/public-advisories?district=Nagpur")
    assert resp.status_code == 200
    data = resp.json()
    for adv in data["advisories"]:
        assert "nagpur" in adv["district"].lower()


def test_filter_advisories_by_evidence_type():
    resp = client.get("/api/v1/public-advisories?evidence_type=GENERAL_PREVENTIVE_ADVISORY")
    assert resp.status_code == 200
    data = resp.json()
    for adv in data["advisories"]:
        assert adv["evidence_type"] == "GENERAL_PREVENTIVE_ADVISORY"


def test_get_advisories_summary():
    resp = client.get("/api/v1/public-advisories/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_documents" in data
    assert "total_advisories" in data
    assert "evidence_type_counts" in data
    assert "crop_counts" in data
    assert "district_counts" in data
    assert data["sources_count"] >= 7


def test_get_advisory_sources():
    resp = client.get("/api/v1/public-advisories/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    source_ids = {s["source_id"] for s in data}
    assert "CROPSAP-PUBLIC" in source_ids
    assert "ICAR-CICR-PUB" in source_ids


def test_get_single_advisory_and_404():
    # First get list to obtain a real ID
    list_resp = client.get("/api/v1/public-advisories?limit=1")
    first_id = list_resp.json()["advisories"][0]["advisory_id"]

    resp = client.get(f"/api/v1/public-advisories/{first_id}")
    assert resp.status_code == 200
    assert resp.json()["advisory_id"] == first_id

    # 404 for non-existent ID
    bad_resp = client.get("/api/v1/public-advisories/NON-EXISTENT-ID")
    assert bad_resp.status_code == 404


def test_submit_human_review():
    list_resp = client.get("/api/v1/public-advisories?limit=1")
    first_id = list_resp.json()["advisories"][0]["advisory_id"]

    payload = {
        "reviewer_id": "TEST-REVIEWER-01",
        "action": "APPROVE",
        "justification": "Verified against institutional publication by automated test suite.",
    }
    resp = client.post(f"/api/v1/public-advisories/{first_id}/review", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["human_review_status"] == "VERIFIED_ADVISORY"
    assert "audit_id" in res_data

