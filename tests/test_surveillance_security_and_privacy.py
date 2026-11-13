"""
tests/test_surveillance_security_and_privacy.py
────────────────────────────────────────────────
Security, privacy, and cryptographic verification test suite for Phase 18:
1. Keyed HMAC-SHA-256 Farmer Pseudonymization (entropy, reproducibility, key rotation).
2. IdentityVault access authorization, lookup, and collision resolution (-C1, -C2).
3. Deterministic spatial displacement (1.5–3.0 km) defeating Law of Large Numbers (LLN) averaging attacks.
4. Public surveillance record sanitization and quasi-identifier suppression.
5. CSV upload payload size limit enforcement (5 MB threshold / HTTP 413).
6. CSV formula injection prevention (CWE-1236 mitigation).
7. Tamper-evident audit log cryptographic hash chaining and integrity verification.
8. Role-based / API-key access gate for unmasked farm coordinates.
"""
from __future__ import annotations

import io
import json
import math
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from src.data_ingestion.pest_surveillance.surveillance_pseudonymization import (
    IdentityVault,
    fuzz_coordinates_deterministic,
    generate_pseudonymous_farmer_id,
    generate_pseudonymous_field_id,
    sanitize_public_surveillance_record,
    MIN_DISPLACEMENT_KM,
    MAX_DISPLACEMENT_KM,
)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    test_dir = tmp_path / "pest_surveillance"
    test_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("backend.app.api.pest_surveillance.DATA_DIR", test_dir)
    monkeypatch.setattr("backend.app.api.pest_surveillance.RAW_DATA_DIR", test_dir / "raw")
    monkeypatch.setattr("backend.app.api.pest_surveillance.STORAGE_FILE", test_dir / "field_surveillance_records.json")
    monkeypatch.setattr("backend.app.api.pest_surveillance.AUDIT_FILE", test_dir / "surveillance_audit_log.json")
    monkeypatch.setenv("SURVEILLANCE_ADMIN_KEY", "TEST_SECRET_RESEARCH_ADMIN_KEY_2027")
    return TestClient(app)


# ==============================================================================
# 1. HMAC-SHA-256 FARMER PSEUDONYMIZATION TESTS
# ==============================================================================

def test_hmac_pseudonymization_determinism():
    """Identical farmer details and key produce the identical pseudonym."""
    id1 = generate_pseudonymous_farmer_id("Ramesh Patil", "74/2A", "Nagpur", "KEY_ALPHA")
    id2 = generate_pseudonymous_farmer_id("Ramesh Patil", "74/2A", "Nagpur", "KEY_ALPHA")
    assert id1 == id2
    assert id1.startswith("FMR-NAG-")
    # Format: FMR-NAG-{12 hex chars} -> total length 8 + 12 = 20
    hex_part = id1.split("-")[2]
    assert len(hex_part) == 12
    # Verify hex characters only
    int(hex_part, 16)


def test_hmac_pseudonymization_entropy_and_key_rotation():
    """Different inputs or rotated secret keys generate distinct pseudonyms."""
    id_base = generate_pseudonymous_farmer_id("Ramesh Patil", "74/2A", "Nagpur", "KEY_ALPHA")
    id_diff_survey = generate_pseudonymous_farmer_id("Ramesh Patil", "74/2B", "Nagpur", "KEY_ALPHA")
    id_diff_key = generate_pseudonymous_farmer_id("Ramesh Patil", "74/2A", "Nagpur", "KEY_BETA")

    assert id_base != id_diff_survey
    assert id_base != id_diff_key


def test_pseudonymous_field_id_hierarchy():
    """Field ID generation adheres to standard hierarchical format MAH-DIST-TAL-PLOT."""
    fid = generate_pseudonymous_field_id("Nagpur", "Katol", 1)
    assert fid == "MAH-NAG-KAT-001"
    fid12 = generate_pseudonymous_field_id("Yavatmal", "Darwha", 12)
    assert fid12 == "MAH-YAV-DAR-012"


# ==============================================================================
# 2. IDENTITY VAULT AUTHORIZATION & COLLISION RESOLUTION TESTS
# ==============================================================================

def test_identity_vault_authorization(tmp_path: Path):
    """Vault requires valid admin token for registration and lookup."""
    vault_file = tmp_path / "vault.json"
    admin_token = "SUPER_SECURE_VAULT_TOKEN"
    vault = IdentityVault(vault_file, admin_token)

    # Unauthorized registration
    with pytest.raises(PermissionError, match="Unauthorized access"):
        vault.register_farmer("Suresh Kale", "101/1", "Amravati", "9876543210", "WRONG_TOKEN")

    # Authorized registration
    fid = vault.register_farmer("Suresh Kale", "101/1", "Amravati", "9876543210", admin_token)
    assert fid.startswith("FMR-AMR-")

    # Unauthorized lookup
    with pytest.raises(PermissionError, match="Unauthorized access"):
        vault.lookup_identity(fid, "WRONG_TOKEN")

    # Authorized lookup
    record = vault.lookup_identity(fid, admin_token)
    assert record is not None
    assert record["legal_name"] == "Suresh Kale"
    assert record["phone_masked"] == "+91-XXXXX-3210"


def test_identity_vault_collision_resolution(tmp_path: Path):
    """If an HMAC collision occurs with a distinct farmer, resolve via -C1 suffix."""
    vault_file = tmp_path / "vault.json"
    admin_token = "VAULT_TOKEN"
    vault = IdentityVault(vault_file, admin_token)

    # Register Farmer 1
    fid1 = vault.register_farmer("Ganesh Raut", "12/1", "Jalgaon", "9111111111", admin_token)

    # Same farmer re-registering returns same ID (idempotency)
    fid1_again = vault.register_farmer("Ganesh Raut", "12/1", "Jalgaon", "9111111111", admin_token)
    assert fid1_again == fid1

    # Simulate an artificial hash collision by manually injecting a collision
    vault._mappings[fid1] = {
        "farmer_id": fid1,
        "legal_name": "Different Farmer",
        "survey_number": "999/X",
        "district_code": "JAL",
    }
    # Register Ganesh Raut again - should detect collision with "Different Farmer" and assign -C1
    resolved_fid = vault.register_farmer("Ganesh Raut", "12/1", "Jalgaon", "9111111111", admin_token)
    assert resolved_fid == f"{fid1}-C1"


# ==============================================================================
# 3. DETERMINISTIC COORDINATE DISPLACEMENT (DEFEATING LLN ATTACKS)
# ==============================================================================

def test_coordinate_fuzzing_bounds_and_determinism():
    """
    Coordinate displacement must be between 1.5 km and 3.0 km.
    Repeated queries must return the EXACT same fuzzed coordinates (defeats averaging attack).
    """
    orig_lat = 21.050000
    orig_lon = 78.950000
    field_id = "MAH-NGP-KAT-001"

    fuzzed_lat1, fuzzed_lon1 = fuzz_coordinates_deterministic(orig_lat, orig_lon, field_id)
    fuzzed_lat2, fuzzed_lon2 = fuzz_coordinates_deterministic(orig_lat, orig_lon, field_id)

    # 1. Strict determinism: 100 queries produce the identical result
    assert fuzzed_lat1 == fuzzed_lat2
    assert fuzzed_lon1 == fuzzed_lon2

    # 2. Approximate planar displacement distance in km
    d_lat_km = (fuzzed_lat1 - orig_lat) * 111.0
    d_lon_km = (fuzzed_lon1 - orig_lon) * 104.3
    dist_km = math.sqrt(d_lat_km ** 2 + d_lon_km ** 2)

    # Must fall within [MIN_DISPLACEMENT_KM, MAX_DISPLACEMENT_KM] (with small margin for rounding to 4 decimals)
    assert MIN_DISPLACEMENT_KM - 0.05 <= dist_km <= MAX_DISPLACEMENT_KM + 0.05

    # 3. LLN Averaging Attack Simulation:
    # If coordinates were jittered with random Gaussian/uniform noise, mean(samples) -> true_coord.
    # Because our engine is deterministic HMAC(field_id), an attacker taking 50 samples gets the same offset:
    samples_lat = [fuzz_coordinates_deterministic(orig_lat, orig_lon, field_id)[0] for _ in range(50)]
    attacker_mean_lat = sum(samples_lat) / len(samples_lat)
    assert abs(attacker_mean_lat - fuzzed_lat1) < 1e-9
    assert abs(attacker_mean_lat - orig_lat) > 0.005  # True location is NOT recovered!


def test_different_fields_get_different_displacements():
    """Different fields at identical coordinates receive distinct spatial offsets."""
    orig_lat = 21.05
    orig_lon = 78.95
    f1_lat, f1_lon = fuzz_coordinates_deterministic(orig_lat, orig_lon, "MAH-NGP-KAT-001")
    f2_lat, f2_lon = fuzz_coordinates_deterministic(orig_lat, orig_lon, "MAH-NGP-KAT-002")
    assert (f1_lat, f1_lon) != (f2_lat, f2_lon)


# ==============================================================================
# 4. PUBLIC RECORD SANITIZATION
# ==============================================================================

def test_sanitize_public_surveillance_record():
    """Sanitization suppresses village name, fuzzes coordinates, and removes reviewer notes."""
    raw_record = {
        "observation_id": "OBS-2027-001",
        "field_id": "MAH-NGP-KAT-001",
        "latitude": 21.0500,
        "longitude": 78.9500,
        "district": "Nagpur",
        "taluka": "Katol",
        "village": "Paradsinga",
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 14.5,
        "plants_sampled": 20,
        "reviewed_by": "DR_ENTOMOLOGIST_PRIVATE_ID",
        "reviewer_notes": "Internal agronomic validation notes",
        "source_document_sha256": "abcdef1234567890",
    }
    sanitized = sanitize_public_surveillance_record(raw_record)

    # Village suppressed
    assert sanitized["village"] == "[SUPPRESSED_FOR_PRIVACY]"
    # Coordinates fuzzed
    assert sanitized["coordinates_fuzzed"] is True
    assert sanitized["latitude"] != raw_record["latitude"]
    assert sanitized["longitude"] != raw_record["longitude"]
    # PII / internal audit fields stripped
    assert "reviewed_by" not in sanitized
    assert "reviewer_notes" not in sanitized
    assert "source_document_sha256" not in sanitized
    # Core agronomic data preserved
    assert sanitized["district"] == "Nagpur"
    assert sanitized["taluka"] == "Katol"
    assert sanitized["crop"] == "cotton"
    assert sanitized["pest_incidence_pct"] == 14.5
    assert sanitized["plants_sampled"] == 20


# ==============================================================================
# 5. CSV UPLOAD SIZE LIMIT ENFORCEMENT (5 MB THRESHOLD)
# ==============================================================================

def test_csv_upload_size_limit_rejection(client: TestClient):
    """Uploading a CSV exceeding 5 MB must be rejected with HTTP 413."""
    # Generate an oversized CSV payload (> 5 MB)
    header = "observation_id,observation_date,district,taluka,village,latitude,longitude,crop,crop_variety,pest_common_name,pest_scientific_name,pest_incidence_pct,pest_severity_pct,trap_type,trap_catch_count,plants_sampled,plants_affected,sampling_method,observation_frequency,sowing_date,crop_growth_stage,days_since_sowing,source_organization,source_document,source_record_id,collection_method,verification_status,data_license\n"
    dummy_row = "OBS-DUMMY,2027-07-01,Nagpur,Katol,Paradsinga,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,10.0,5.0,delta_trap,5.0,20,2,fixed_plot_scouting,weekly,2027-06-15,Squaring,16,AgriAdapt,batch.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
    # 5 MB = 5,242,880 bytes. Repeat dummy row enough times to exceed 5.1 MB:
    oversized_data = (header + dummy_row * 20000).encode("utf-8")
    assert len(oversized_data) > 5 * 1024 * 1024

    files = {"file": ("oversized_surveillance.csv", io.BytesIO(oversized_data), "text/csv")}
    resp = client.post("/api/v1/pest-surveillance/upload-csv", files=files)
    assert resp.status_code == 413
    assert "exceeds maximum permitted size of 5 MB" in resp.json()["detail"]


# ==============================================================================
# 6. CSV FORMULA INJECTION PREVENTION (CWE-1236)
# ==============================================================================

def test_csv_formula_injection_sanitization(client: TestClient):
    """CSV cells beginning with =, +, -, @ must be neutralized to prevent formula execution."""
    malicious_csv = (
        "observation_id,observation_date,district,taluka,village,latitude,longitude,crop,crop_variety,pest_common_name,pest_scientific_name,pest_incidence_pct,pest_severity_pct,trap_type,trap_catch_count,plants_sampled,plants_affected,sampling_method,observation_frequency,sowing_date,crop_growth_stage,days_since_sowing,source_organization,source_document,source_record_id,collection_method,verification_status,data_license\n"
        "=CMD|' /C calc'!A0,2027-07-01,Nagpur,Katol,Paradsinga,21.05,78.95,cotton,RCH-659,Pink Bollworm,Pectinophora gossypiella,10.0,5.0,delta_trap,5.0,20,2,fixed_plot_scouting,weekly,2027-06-15,Squaring,16,AgriAdapt,batch.csv,1,field_scouting_visual,UNVERIFIED,GOVERNMENT_RESTRICTED\n"
    )
    files = {"file": ("injection_test.csv", io.BytesIO(malicious_csv.encode("utf-8")), "text/csv")}
    resp = client.post("/api/v1/pest-surveillance/upload-csv", files=files)
    assert resp.status_code == 200

    # Retrieve records with admin key to check stored representation
    rec_resp = client.get(
        "/api/v1/pest-surveillance/records?fuzz_coordinates=false",
        headers={"X-API-Key": "TEST_SECRET_RESEARCH_ADMIN_KEY_2027"},
    )
    records = rec_resp.json()["records"]
    target = next(r for r in records if "calc" in str(r.get("observation_id")))
    # Formula execution prefix must be neutralized with a leading single quote
    assert target["observation_id"].startswith("'=CMD")


# ==============================================================================
# 7. AUDIT LOG CRYPTOGRAPHIC HASH CHAINING & INTEGRITY VERIFICATION
# ==============================================================================

def test_audit_log_hash_chain_and_tamper_detection(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Audit log must form an unbroken SHA-256 hash chain and report post-hoc tampering."""
    # 1. Create two observations and review them
    obs1 = {
        "observation_id": "OBS-AUD-001",
        "observation_date": "2027-07-01",
        "district": "Nagpur",
        "latitude": 21.05,
        "longitude": 78.95,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 8.0,
        "plants_sampled": 20,
        "plants_affected": 2,
        "is_draft": False,
    }
    obs2 = {
        "observation_id": "OBS-AUD-002",
        "observation_date": "2027-07-08",
        "district": "Amravati",
        "latitude": 20.93,
        "longitude": 77.75,
        "crop": "soybean",
        "pest_common_name": "Tobacco Caterpillar",
        "pest_incidence_pct": 12.0,
        "plants_sampled": 20,
        "plants_affected": 3,
        "is_draft": False,
    }
    client.post("/api/v1/pest-surveillance/records", json=obs1)
    client.post("/api/v1/pest-surveillance/records", json=obs2)

    # Perform reviews
    rev1 = {
        "observation_id": "OBS-AUD-001",
        "reviewer_id": "DR_ENTOMOLOGIST_1",
        "action": "APPROVE",
        "justification": "Checked boll dissection counts; confirmed valid.",
    }
    rev2 = {
        "observation_id": "OBS-AUD-002",
        "reviewer_id": "DR_ENTOMOLOGIST_2",
        "action": "APPROVE",
        "justification": "Defoliation and sweep counts verified.",
    }
    client.post("/api/v1/pest-surveillance/review", json=rev1)
    client.post("/api/v1/pest-surveillance/review", json=rev2)

    # Verify audit chain integrity via API endpoint
    verify_resp = client.get("/api/v1/pest-surveillance/audit-log/verify")
    assert verify_resp.status_code == 200
    vdata = verify_resp.json()
    assert vdata["is_valid"] is True
    assert vdata["total_entries"] == 2
    assert vdata["verified_entries"] == 2

    # Now simulate tampering: directly alter the audit file on disk
    audit_file = tmp_path / "pest_surveillance" / "surveillance_audit_log.json"
    with open(audit_file, "r", encoding="utf-8") as f:
        log = json.load(f)
    # Alter justification of first entry without updating entry_hash
    log[0]["justification"] = "Tampered justification after the fact!"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    # Verify endpoint must catch tampering!
    tamper_resp = client.get("/api/v1/pest-surveillance/audit-log/verify")
    assert tamper_resp.status_code == 200
    tdata = tamper_resp.json()
    assert tdata["is_valid"] is False
    assert tdata["tampered_at_index"] == 0
    assert "Tampering detected at index 0" in tdata["message"]


# ==============================================================================
# 8. RESTRICTED ACCESS TO UNMASKED FARM COORDINATES
# ==============================================================================

def test_access_controls_for_unmasked_coordinates(client: TestClient):
    """
    Public access gets fuzzed coordinates by default.
    Unmasked coordinates require valid X-API-Key authorization.
    """
    # Create a test observation
    obs = {
        "observation_id": "OBS-PRIV-001",
        "observation_date": "2027-08-01",
        "district": "Yavatmal",
        "taluka": "Darwha",
        "village": "Lohara",
        "latitude": 20.3200,
        "longitude": 77.7600,
        "crop": "cotton",
        "pest_common_name": "Pink Bollworm",
        "pest_incidence_pct": 11.0,
        "plants_sampled": 20,
        "plants_affected": 2,
        "is_draft": False,
    }
    client.post("/api/v1/pest-surveillance/records", json=obs)

    # 1. Default public query (fuzz_coordinates defaults to True)
    pub_resp = client.get("/api/v1/pest-surveillance/records")
    assert pub_resp.status_code == 200
    pub_data = pub_resp.json()
    rec = next(r for r in pub_data["records"] if r["observation_id"] == "OBS-PRIV-001")
    assert rec["coordinates_fuzzed"] is True
    assert rec["village"] == "[SUPPRESSED_FOR_PRIVACY]"
    assert rec["latitude"] != 20.3200  # displaced

    # 2. Querying unmasked coordinates without API key must return 403 Forbidden
    unauth_resp = client.get("/api/v1/pest-surveillance/records?fuzz_coordinates=false")
    assert unauth_resp.status_code == 403
    assert "requires valid researcher authorization" in unauth_resp.json()["detail"]

    # 3. Querying unmasked coordinates with incorrect API key must return 403 Forbidden
    wrong_key_resp = client.get(
        "/api/v1/pest-surveillance/records?fuzz_coordinates=false",
        headers={"X-API-Key": "INVALID_KEY_123"},
    )
    assert wrong_key_resp.status_code == 403

    # 4. Querying unmasked coordinates with valid API key returns exact farm location
    auth_resp = client.get(
        "/api/v1/pest-surveillance/records?fuzz_coordinates=false",
        headers={"X-API-Key": "TEST_SECRET_RESEARCH_ADMIN_KEY_2027"},
    )
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    auth_rec = next(r for r in auth_data["records"] if r["observation_id"] == "OBS-PRIV-001")
    assert auth_rec["latitude"] == 20.3200
    assert auth_rec["longitude"] == 77.7600
    assert auth_rec["village"] == "Lohara"
