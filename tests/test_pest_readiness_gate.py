"""
tests/test_pest_readiness_gate.py
─────────────────────────────────
Test suite for the Centralized Production ML Readiness Gate:
- Verification that gate returns BLOCKED on the initial data repository
- Independent verification of all 11 scientific criteria
- Data foundation inventory integrity across all 5 data streams
- Invariant enforcement: synthetic or quarantined data contamination detection
- API endpoint validation: GET /api/v1/pest-surveillance/readiness-gate
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from src.pest_risk.production_readiness_gate import (
    evaluate_production_readiness,
    MINIMUM_AUTHENTIC_RECORDS,
    MINIMUM_POSITIVE_LABELS,
    MINIMUM_NEGATIVE_LABELS,
    MINIMUM_SEASONS,
    MINIMUM_DISTRICTS,
    TARGET_ETLS,
)


def test_evaluate_production_readiness_default_blocked():
    """Gate must return BLOCKED and is_ready_for_training=False in the initial project state."""
    report = evaluate_production_readiness()

    assert report.gate_status == "BLOCKED"
    assert report.is_ready_for_training is False
    assert len(report.blocking_reasons) == 10

    # Verify 11 criteria evaluated
    assert len(report.criteria) == 11

    # Check that storage isolation is satisfied (clean store, 0 contamination)
    isolation_crit = next(c for c in report.criteria if c["name"] == "Production Storage Isolation Guarantee")
    assert isolation_crit["is_satisfied"] is True
    assert isolation_crit["blocking_reason"] is None

    # Check that authentic field surveillance count is unsatisfied
    count_crit = next(c for c in report.criteria if c["name"] == "Authentic Commercial Field Surveillance Count")
    assert count_crit["is_satisfied"] is False
    assert count_crit["actual_state"] == 0


def test_data_foundation_inventory_counts():
    """Verify that the data foundation inventory accurately reports all 5 data streams."""
    report = evaluate_production_readiness()
    inv = report.data_foundation_inventory

    assert inv["environmental_records"] == 612
    assert inv["public_advisories"] == 49
    assert inv["quarantined_historical_observations"] == 13
    assert inv["synthetic_benchmark_records"] == 100000
    assert inv["authentic_prospective_surveillance_records"] == 0
    assert inv["verified_positive_outbreak_labels"] == 0
    assert inv["verified_negative_observation_windows"] == 0


def test_readiness_gate_insufficient_records_simulation(tmp_path: Path):
    """Even if some records are acquired, gate remains BLOCKED if under 500 records."""
    mock_file = tmp_path / "mock_surveillance.json"
    mock_data = [
        {
            "observation_id": f"OBS-{i:03d}",
            "crop": "cotton",
            "pest_common_name": "Pink Bollworm",
            "district": "Nagpur",
            "field_id": f"FIELD-{i % 5}",
            "season_year": "2026-Kharif",
            "sampling_method": "destructive_boll_dissection",
            "outbreak_label": 1 if i % 2 == 0 else 0,
            "verification_status": "FIELD_SCOUT_VERIFIED",
            "photo_evidence_sha256": "abcdef1234567890",
            "farmer_id": "FARMER-01",
            "is_draft": False,
        }
        for i in range(25)
    ]
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    report = evaluate_production_readiness(surveillance_path=mock_file)
    assert report.gate_status == "BLOCKED"
    assert report.is_ready_for_training is False
    assert any("Insufficient authentic records: 25 acquired" in r for r in report.blocking_reasons)


def test_readiness_gate_unverified_etls_blocks_training(tmp_path: Path):
    """Unverified ETL status blocks production training even if observation thresholds were met."""
    mock_file = tmp_path / "mock_surveillance_500.json"
    districts = ["Nagpur", "Amravati", "Yavatmal", "Jalgaon"]
    crops_pests = [
        ("cotton", "Pink Bollworm"),
        ("cotton", "American Bollworm"),
        ("soybean", "Tobacco Caterpillar"),
        ("rice", "Brown Plant Hopper"),
        ("maize", "Fall Armyworm"),
    ]
    mock_data = []
    for i in range(500):
        cp = crops_pests[i % len(crops_pests)]
        mock_data.append({
            "observation_id": f"OBS-{i:04d}",
            "crop": cp[0],
            "pest_common_name": cp[1],
            "district": districts[i % len(districts)],
            "field_id": f"FIELD-{i % 25}",
            "season_year": f"2026-Season-{i % 2}",
            "sampling_method": "drop_cloth_count",
            "outbreak_label": 1 if i < 100 else 0,
            "verification_status": "KVK_EXPERT_VALIDATED",
            "photo_evidence_sha256": "sha256_mock_hash",
            "farmer_id": f"FARMER-{i % 25}",
            "is_draft": False,
        })
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    # When ETLs remain at PRIMARY_SOURCE_RETRIEVED
    unverified_etls = {k: "PRIMARY_SOURCE_RETRIEVED" for k in TARGET_ETLS}
    report = evaluate_production_readiness(surveillance_path=mock_file, etl_status_map=unverified_etls)
    assert report.gate_status == "BLOCKED"
    assert report.is_ready_for_training is False
    assert any("ETL verification incomplete" in r for r in report.blocking_reasons)

    # When all ETLs are VERIFIED and all 500 records satisfy conditions:
    verified_etls = {k: "VERIFIED" for k in TARGET_ETLS}
    approved_report = evaluate_production_readiness(surveillance_path=mock_file, etl_status_map=verified_etls)
    assert approved_report.gate_status == "READY"
    assert approved_report.is_ready_for_training is True
    assert len(approved_report.blocking_reasons) == 0


def test_readiness_gate_contamination_detection(tmp_path: Path):
    """Gate detects synthetic benchmark or historical quarantined records mixed into surveillance store."""
    mock_file = tmp_path / "contaminated_surveillance.json"
    mock_data = [
        {
            "observation_id": "CONTAMINATED-01",
            "crop": "cotton",
            "pest_common_name": "Pink Bollworm",
            "dataset_classification": "SYNTHETIC_BENCHMARK",
            "is_draft": False,
        }
    ]
    with open(mock_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)

    report = evaluate_production_readiness(surveillance_path=mock_file)
    assert report.gate_status == "BLOCKED"
    assert any("Contamination detected" in r for r in report.blocking_reasons)
    isolation_crit = next(c for c in report.criteria if c["name"] == "Production Storage Isolation Guarantee")
    assert isolation_crit["is_satisfied"] is False


def test_api_readiness_gate_endpoint():
    """Verify that the FastAPI endpoint GET /api/v1/pest-surveillance/readiness-gate returns HTTP 200 BLOCKED."""
    client = TestClient(app)
    response = client.get("/api/v1/pest-surveillance/readiness-gate")

    assert response.status_code == 200
    data = response.json()
    assert data["gate_status"] == "BLOCKED"
    assert data["is_ready_for_training"] is False
    assert "evaluation_timestamp" in data
    assert len(data["blocking_reasons"]) == 10
    assert len(data["criteria"]) == 11
    assert data["data_foundation_inventory"]["environmental_records"] == 612
    assert data["data_foundation_inventory"]["public_advisories"] == 49
    assert data["data_foundation_inventory"]["quarantined_historical_observations"] == 13
    assert data["data_foundation_inventory"]["synthetic_benchmark_records"] == 100000
    assert data["data_foundation_inventory"]["authentic_prospective_surveillance_records"] == 0
