"""
tests/test_surveillance_pipeline.py
───────────────────────────────────
Comprehensive test suite for Phase 6 authentic pest surveillance
data acquisition, validation, geospatial matching, temporal alignment,
and ground-truth labeling pipeline.

Phase 7 additions:
  - test_etl_verification_status_field_exists: All registered ETLs must carry a
    verification_status field that is one of VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED.
  - test_unverified_etl_blocks_labeling: An ETL with verification_status="UNVERIFIED"
    must return label_status="ETL_UNVERIFIED" and outbreak_label_7d=None.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from src.data_ingestion.pest_surveillance import (
    HIGH_CONFIDENCE_GRID_DISTANCE_KM,
    KNOWN_DISTRICT_CENTROIDS,
    MAX_PERMISSIBLE_MATCH_DISTANCE_KM,
    EconomicThreshold,
    GeospatialMatch,
    LoadResult,
    OutbreakLabelResult,
    SurveillanceRecord,
    calculate_smw,
    compute_file_sha256,
    compute_forward_outbreak_label,
    extract_antecedent_environmental_features,
    get_economic_threshold,
    haversine_distance_km,
    list_authoritative_sources,
    load_surveillance_file,
    match_observation_to_environmental_grid,
    validate_surveillance_records,
)
from src.data_ingestion.pest_surveillance.surveillance_labeling import OFFICIAL_ETL_REGISTRY

DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "aligned_environmental_surveillance_2023-06-01_2023-10-31.csv"
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. SOURCES AUDIT & ACCESS REQUIREMENTS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_authoritative_sources_registry():
    sources = list_authoritative_sources()
    assert len(sources) == 4
    source_ids = {s.source_id for s in sources}
    assert "CROPSAP-MAHA" in source_ids
    assert "ICAR-NCIPM" in source_ids
    assert "ICAR-CICR" in source_ids
    assert "MAHA-SAUS" in source_ids

    # Every source must honestly report that raw micro-data is NOT publicly downloadable
    for src in sources:
        assert src.is_publicly_downloadable is False
        assert src.requires_institutional_agreement is True
        assert len(src.data_sharing_requirements) >= 2


# ══════════════════════════════════════════════════════════════════════════════
# 2. SCHEMA & PHYSICAL BOUNDS TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_surveillance_record_valid_parsing():
    record = SurveillanceRecord(
        observation_id="OBS-001",
        observation_date="2023-07-15",
        district="Nagpur",
        taluka="Hingna",
        village="Kanhan",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        crop_variety="Bt BG-II",
        pest_common_name="Pink Bollworm",
        pest_scientific_name="Pectinophora gossypiella",
        pest_incidence_pct=8.5,
        pest_severity_pct=4.2,
        trap_type="pheromone_delta",
        trap_catch_count=12.0,
        plants_sampled=20,
        plants_affected=2,
        sampling_method="fixed_plot_scouting",
        observation_frequency="weekly",
        sowing_date="2023-06-15",
        crop_growth_stage="squaring",
        days_since_sowing=30,
        source_organization="CROPSAP-Maharashtra",
        verification_status="FIELD_SCOUT_VERIFIED",
        data_license="GOVERNMENT_RESTRICTED",
    )
    assert record.observation_id == "OBS-001"
    assert record.pest_incidence_pct == 8.5
    assert record.trap_catch_count == 12.0


def test_surveillance_record_outside_maharashtra_rejected():
    with pytest.raises(ValidationError, match="outside Maharashtra bounding box"):
        SurveillanceRecord(
            observation_id="OBS-DELHI",
            observation_date="2023-07-15",
            district="New Delhi",
            latitude=28.61,  # Latitude of Delhi (outside Maharashtra 15.6-22.1)
            longitude=77.20,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=5.0,
            source_organization="TEST",
        )


def test_surveillance_record_physical_range_violations_rejected():
    # Incidence > 100%
    with pytest.raises(ValidationError, match="pest_incidence_pct must be between 0.0 and 100.0%"):
        SurveillanceRecord(
            observation_id="OBS-BAD-INC",
            observation_date="2023-07-15",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=105.0,
            source_organization="TEST",
        )

    # Plants affected > plants sampled
    with pytest.raises(ValidationError, match="cannot exceed plants_sampled"):
        SurveillanceRecord(
            observation_id="OBS-BAD-COUNTS",
            observation_date="2023-07-15",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            plants_sampled=20,
            plants_affected=25,
            source_organization="TEST",
        )


def test_surveillance_record_crop_pest_biological_mismatch_rejected():
    # Pink bollworm does NOT attack soybean
    with pytest.raises(ValidationError, match="Biologically invalid or unmonitored"):
        SurveillanceRecord(
            observation_id="OBS-MISMATCH",
            observation_date="2023-07-15",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="soybean",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=5.0,
            source_organization="TEST",
        )


def test_surveillance_record_requires_at_least_one_quantitative_measure():
    with pytest.raises(ValidationError, match="must contain at least one quantitative measurement"):
        SurveillanceRecord(
            observation_id="OBS-EMPTY-MEASURE",
            observation_date="2023-07-15",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=None,
            pest_severity_pct=None,
            trap_catch_count=None,
            source_organization="TEST",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 3. LOADER & HASH PROVENANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_surveillance_loader_handles_aliases_and_preserves_missing_values(tmp_path: Path):
    csv_file = tmp_path / "test_surveillance_export.csv"
    csv_file.write_text(
        "obs_id,date,dist,taluk,lat,lon,host_crop,pest,incidence,moths_count,growth_stage\n"
        "REC-1,2023-07-10,Nagpur,Hingna,21.14,79.05,cotton,Pink Bollworm,5.5,12.0,squaring\n"
        "REC-2,2023-07-17,Nagpur,Hingna,21.14,79.05,cotton,Pink Bollworm,12.0,,flowering\n"  # missing moths_count
    )

    load_res: LoadResult = load_surveillance_file(csv_file)
    assert load_res.total_raw_rows == 2
    assert len(load_res.loaded_records) == 2
    assert len(load_res.file_sha256) == 64  # Valid SHA-256

    rec2 = load_res.loaded_records[1]
    # Check that missing moths_count remains None, NOT zero!
    assert rec2["trap_catch_count"] is None
    assert rec2["pest_incidence_pct"] == 12.0


# ══════════════════════════════════════════════════════════════════════════════
# 4. VALIDATION & DUPLICATE DETECTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_validation_detects_duplicates_and_aggregates_distributions():
    records_payload = [
        {
            "observation_id": "REC-A",
            "observation_date": "2023-08-01",
            "district": "Nagpur",
            "taluka": "Hingna",
            "latitude": 21.15,
            "longitude": 79.08,
            "crop": "cotton",
            "pest_common_name": "Pink Bollworm",
            "pest_incidence_pct": 5.0,
            "source_organization": "CROPSAP",
        },
        # Duplicate of REC-A
        {
            "observation_id": "REC-A-DUP",
            "observation_date": "2023-08-01",
            "district": "Nagpur",
            "taluka": "Hingna",
            "latitude": 21.15,
            "longitude": 79.08,
            "crop": "cotton",
            "pest_common_name": "Pink Bollworm",
            "pest_incidence_pct": 5.0,
            "source_organization": "CROPSAP",
        },
        # Valid distinct record
        {
            "observation_id": "REC-B",
            "observation_date": "2023-08-01",
            "district": "Amravati",
            "taluka": "Chandur",
            "latitude": 20.92,
            "longitude": 77.77,
            "crop": "soybean",
            "pest_common_name": "Tobacco Caterpillar",
            "pest_incidence_pct": 8.0,
            "source_organization": "CROPSAP",
        },
    ]

    valid_records, report = validate_surveillance_records(records_payload)
    assert len(valid_records) == 2
    assert report.duplicate_count == 1
    assert report.crop_distribution["cotton"] == 1
    assert report.crop_distribution["soybean"] == 1
    assert report.species_distribution["pink_bollworm"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# 5. GEOSPATIAL MATCHING & DISTANCE LIMIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_geospatial_matching_success_and_rejection():
    # Near Nagpur centroid (Kanhan)
    rec_near = SurveillanceRecord(
        observation_id="NEAR-NGP",
        observation_date="2023-07-15",
        district="Nagpur",
        latitude=21.14,
        longitude=79.09,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=5.0,
        source_organization="TEST",
    )
    match_near = match_observation_to_environmental_grid(rec_near)
    assert match_near.is_matched is True
    assert match_near.matched_environmental_location == "Nagpur"
    assert match_near.distance_km < HIGH_CONFIDENCE_GRID_DISTANCE_KM
    assert match_near.spatial_confidence == "HIGH_CONFIDENCE_GRID"

    # Distant location in Konkan/Western Maharashtra far from the 4 Vidarbha/Khandesh stations
    rec_far = SurveillanceRecord(
        observation_id="FAR-RATNAGIRI",
        observation_date="2023-07-15",
        district="Ratnagiri",
        latitude=16.99,
        longitude=73.30,
        crop="rice",
        pest_common_name="Brown Planthopper",
        pest_incidence_pct=5.0,
        source_organization="TEST",
    )
    match_far = match_observation_to_environmental_grid(rec_far)
    assert match_far.is_matched is False
    assert match_far.spatial_confidence == "SPATIAL_MISMATCH"
    assert "exceeding maximum permissible spatial tolerance" in match_far.notes


# ══════════════════════════════════════════════════════════════════════════════
# 6. TEMPORAL ALIGNMENT & IMD SMW TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_calculate_smw_imd_standard():
    assert calculate_smw("2023-01-01") == 1
    assert calculate_smw("2023-01-07") == 1
    assert calculate_smw("2023-01-08") == 2
    assert calculate_smw("2023-07-15") == 28
    assert calculate_smw("2023-12-31") == 52


def test_extract_antecedent_environmental_features_without_leakage():
    if not DATASET_PATH.exists():
        pytest.skip(f"Processed dataset not present at {DATASET_PATH}")

    df_env = pd.read_csv(DATASET_PATH)

    rec = SurveillanceRecord(
        observation_id="SCOUT-NGP-2023-08-15",
        observation_date="2023-08-15",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=6.0,
        source_organization="TEST",
    )

    feat = extract_antecedent_environmental_features(
        record=rec,
        matched_location="Nagpur",
        environmental_df=df_env,
        base_temp_c=12.0,
    )

    assert feat.observation_date == "2023-08-15"
    assert feat.smw == 33
    assert feat.antecedent_window_days == 7
    assert feat.t7_mean_temp_c > 20.0
    assert feat.t7_mean_rh_pct > 60.0
    assert feat.temporal_coverage_complete is True


# ══════════════════════════════════════════════════════════════════════════════
# 7. OUTBREAK LABELING PROTOCOL & LEAKAGE PREVENTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_outbreak_labeling_positive_exceeds_etl():
    ref_rec = SurveillanceRecord(
        observation_id="REF-T0",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=4.0,  # Below ETL at T0
        source_organization="CROPSAP",
    )

    # Subsequent visit at T0 + 5 days reporting 14.0% incidence (>= 10% ETL)
    future_rec = SurveillanceRecord(
        observation_id="FUT-T5",
        observation_date="2023-08-06",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=14.0,
        source_organization="CROPSAP",
    )

    label_res: OutbreakLabelResult = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, future_rec],
        forward_days=7,
    )

    assert label_res.outbreak_label_7d == 1
    assert label_res.label_status == "LABELED_OUTBREAK"
    assert label_res.max_forward_incidence_pct == 14.0
    assert ">= ETL" in label_res.notes


def test_outbreak_labeling_verified_negative_scouting():
    ref_rec = SurveillanceRecord(
        observation_id="REF-T0",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=3.0,
        source_organization="CROPSAP",
    )

    # Subsequent visit at T0 + 6 days reporting 4.0% incidence (< 10% ETL)
    future_rec = SurveillanceRecord(
        observation_id="FUT-T6",
        observation_date="2023-08-07",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=4.0,
        source_organization="CROPSAP",
    )

    label_res: OutbreakLabelResult = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, future_rec],
        forward_days=7,
    )

    assert label_res.outbreak_label_7d == 0
    assert label_res.label_status == "LABELED_NON_OUTBREAK"
    assert label_res.max_forward_incidence_pct == 4.0


def test_outbreak_labeling_unobserved_future_remains_none():
    ref_rec = SurveillanceRecord(
        observation_id="REF-LONELY",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=3.0,
        source_organization="CROPSAP",
    )

    # No subsequent visits in [T+1, T+7]
    label_res: OutbreakLabelResult = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec],
        forward_days=7,
    )

    # STRICT RULE: Must NOT be imputed as 0!
    assert label_res.outbreak_label_7d is None
    assert label_res.label_status == "UNOBSERVED_FUTURE_WINDOW"
    assert "No authentic surveillance records found" in label_res.notes


# ══════════════════════════════════════════════════════════════════════════════
# 8. PHASE 7 — ETL VERIFICATION STATUS TESTS (Scientific Governance)
# ══════════════════════════════════════════════════════════════════════════════

def test_etl_verification_status_field_exists_on_all_registered_etls():
    """
    Phase 7 & Phase 13: Every registered ETL must carry a valid verification_status
    field from VALID_ETL_VERIFICATION_STATUSES.
    In Phase 13, all 5 target ETLs have been elevated to PRIMARY_SOURCE_RETRIEVED
    with primary institutional citations.
    """
    from src.data_ingestion.pest_surveillance.surveillance_labeling import (
        OFFICIAL_ETL_REGISTRY,
        VALID_ETL_VERIFICATION_STATUSES,
    )

    assert len(OFFICIAL_ETL_REGISTRY) >= 5, "Expected at least 5 registered ETLs."

    for key, etl in OFFICIAL_ETL_REGISTRY.items():
        assert hasattr(etl, "verification_status"), (
            f"ETL for {key} is missing 'verification_status' field."
        )
        assert etl.verification_status in VALID_ETL_VERIFICATION_STATUSES, (
            f"ETL for {key} has invalid verification_status='{etl.verification_status}'. "
            f"Must be one of {sorted(VALID_ETL_VERIFICATION_STATUSES)}."
        )
        # In Phase 13, all 5 target ETLs have retrieved primary sources
        assert etl.verification_status == "PRIMARY_SOURCE_RETRIEVED", (
            f"ETL for {key} expected PRIMARY_SOURCE_RETRIEVED, got {etl.verification_status}"
        )


def test_production_mode_blocks_non_fully_verified_etls():
    """
    Phase 13: When require_fully_verified_etl=True (production mode), any ETL that is
    not 'VERIFIED' (such as PRIMARY_SOURCE_RETRIEVED) must return label_status='ETL_NOT_PRODUCTION_VERIFIED'
    and outbreak_label_7d=None to prevent uncertified model training.
    """
    from src.data_ingestion.pest_surveillance.surveillance_labeling import (
        compute_forward_outbreak_label,
    )

    ref_rec = SurveillanceRecord(
        observation_id="PROD-TEST-T0",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=4.0,
        source_organization="TEST",
    )
    future_rec = SurveillanceRecord(
        observation_id="PROD-TEST-FUT",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=25.0,  # Exceeds the 10% ETL
        source_organization="TEST",
    )

    # In production mode (require_fully_verified_etl=True), PRIMARY_SOURCE_RETRIEVED is blocked
    result_prod = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, future_rec],
        forward_days=7,
        require_fully_verified_etl=True,
    )
    assert result_prod.outbreak_label_7d is None
    assert result_prod.label_status == "ETL_NOT_PRODUCTION_VERIFIED"
    assert "require_fully_verified_etl=True" in result_prod.notes

    # In exploratory mode (require_fully_verified_etl=False), PRIMARY_SOURCE_RETRIEVED generates label
    result_exp = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, future_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert result_exp.outbreak_label_7d == 1
    assert result_exp.label_status == "LABELED_OUTBREAK"


def test_unverified_etl_blocks_labeling():
    """
    Phase 7: An ETL with verification_status='UNVERIFIED' must NOT generate any
    labeling decision. The function must return outbreak_label_7d=None and
    label_status='ETL_UNVERIFIED', regardless of forward observation values.

    Strategy: Directly instantiate an EconomicThreshold with UNVERIFIED status and
    inject it into the registry for a real crop-pest pair that passes schema validation,
    then restore the original after the test.
    """
    from src.data_ingestion.pest_surveillance.surveillance_labeling import (
        EconomicThreshold,
        OFFICIAL_ETL_REGISTRY,
        compute_forward_outbreak_label,
    )

    test_key = ("cotton", "pink_bollworm")
    original_etl = OFFICIAL_ETL_REGISTRY[test_key]

    # Temporarily replace with UNVERIFIED version
    unverified_etl = EconomicThreshold(
        crop=original_etl.crop,
        pest_id=original_etl.pest_id,
        incidence_etl_pct=original_etl.incidence_etl_pct,
        trap_catch_etl_moths=original_etl.trap_catch_etl_moths,
        threshold_description=original_etl.threshold_description,
        source_authority=original_etl.source_authority,
        verification_status="UNVERIFIED",
    )
    OFFICIAL_ETL_REGISTRY[test_key] = unverified_etl

    try:
        ref_rec = SurveillanceRecord(
            observation_id="UNVERIFIED-TEST-T0",
            observation_date="2023-08-01",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=4.0,
            source_organization="TEST",
        )
        future_rec = SurveillanceRecord(
            observation_id="UNVERIFIED-TEST-FUT",
            observation_date="2023-08-05",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=20.0,  # Exceeds the ETL — but ETL is UNVERIFIED
            source_organization="TEST",
        )
        result = compute_forward_outbreak_label(
            record=ref_rec,
            longitudinal_surveillance_records=[ref_rec, future_rec],
            forward_days=7,
        )

        assert result.outbreak_label_7d is None, (
            "UNVERIFIED ETL must NOT produce a label (expected None)."
        )
        assert result.label_status == "ETL_UNVERIFIED", (
            f"Expected label_status='ETL_UNVERIFIED', got '{result.label_status}'."
        )
        assert "UNVERIFIED" in result.notes, (
            "Result notes must mention UNVERIFIED status."
        )
    finally:
        # Restore original ETL — do not leave test state polluting global registry
        OFFICIAL_ETL_REGISTRY[test_key] = original_etl


def test_surveillance_sources_have_contact_verification_fields():
    """
    Phase 7: All surveillance sources must carry is_contact_verified and
    contact_verification_note fields to support institutional outreach governance.
    """
    sources = list_authoritative_sources()
    for src in sources:
        assert hasattr(src, "is_contact_verified"), (
            f"Source '{src.source_id}' missing 'is_contact_verified' field."
        )
        assert hasattr(src, "contact_verification_note"), (
            f"Source '{src.source_id}' missing 'contact_verification_note' field."
        )
        assert isinstance(src.is_contact_verified, bool), (
            f"Source '{src.source_id}' is_contact_verified must be bool."
        )
        assert len(src.contact_verification_note) > 20, (
            f"Source '{src.source_id}' contact_verification_note is too short to be meaningful."
        )


# ══════════════════════════════════════════════════════════════════════════════
# 9. PHASE 14 — ADVANCED ETL AGRONOMIC RULES & DATASET SEPARATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_dataset_classification_field_enforcement():
    """
    Phase 14: SurveillanceRecord must support explicit dataset_classification
    distinguishing HISTORICAL_RESEARCH_TRIAL from PROSPECTIVE_SENTINEL_FIELD.
    """
    from src.data_ingestion.pest_surveillance.surveillance_schema import (
        VALID_DATASET_CLASSIFICATIONS,
        SurveillanceRecord,
    )

    rec = SurveillanceRecord(
        observation_id="HIST-TRIAL-001",
        observation_date="2023-08-10",
        district="Akola",
        latitude=20.704,
        longitude=77.029,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=6.5,
        source_organization="DR_PDKV_AKOLA",
        dataset_classification="HISTORICAL_RESEARCH_TRIAL",
    )
    assert rec.dataset_classification == "HISTORICAL_RESEARCH_TRIAL"
    assert rec.dataset_classification in VALID_DATASET_CLASSIFICATIONS

    # Invalid classification must be rejected
    with pytest.raises(ValidationError):
        SurveillanceRecord(
            observation_id="INVALID-CLASS-001",
            observation_date="2023-08-10",
            district="Akola",
            latitude=20.704,
            longitude=77.029,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=6.5,
            source_organization="TEST",
            dataset_classification="FABRICATED_FIELD_DATA",
        )


def test_stage_specific_threshold_soybean_flowering():
    """
    Phase 14: Soybean tobacco caterpillar threshold drops from 25% (vegetative)
    to 20% (flowering) due to flower abortion risks. An observation at 22% incidence
    must trigger an outbreak if forward observation is during flowering, but remain
    sub-ETL if during vegetative stage.
    """
    ref_rec = SurveillanceRecord(
        observation_id="SOY-REF-T0",
        observation_date="2023-07-20",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="soybean",
        pest_common_name="Tobacco Caterpillar",
        pest_incidence_pct=5.0,
        source_organization="TEST",
    )

    # Future record at flowering stage with 22% incidence (exceeds flowering 20% ETL)
    fut_flowering = SurveillanceRecord(
        observation_id="SOY-FUT-FLOW",
        observation_date="2023-07-25",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="soybean",
        pest_common_name="Tobacco Caterpillar",
        pest_incidence_pct=22.0,
        crop_growth_stage="flowering",
        source_organization="TEST",
    )
    res_flowering = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_flowering],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res_flowering.outbreak_label_7d == 1
    assert res_flowering.label_status == "LABELED_OUTBREAK"
    assert "flowering" in res_flowering.notes

    # Future record at vegetative stage with 22% incidence (sub-ETL since vegetative ETL is 25%)
    fut_vegetative = SurveillanceRecord(
        observation_id="SOY-FUT-VEG",
        observation_date="2023-07-25",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="soybean",
        pest_common_name="Tobacco Caterpillar",
        pest_incidence_pct=22.0,
        crop_growth_stage="vegetative",
        source_organization="TEST",
    )
    res_vegetative = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_vegetative],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res_vegetative.outbreak_label_7d == 0
    assert res_vegetative.label_status == "LABELED_NON_OUTBREAK"


def test_stage_specific_threshold_maize_seedling():
    """
    Phase 14: Maize FAW threshold is 5% at seedling stage (VE-V2) and 10% at mid-whorl.
    An observation of 7% whorl damage triggers an outbreak at seedling, but is sub-ETL
    at vegetative/mid-whorl.
    """
    ref_rec = SurveillanceRecord(
        observation_id="MAIZE-REF-T0",
        observation_date="2023-07-10",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="maize",
        pest_common_name="Fall Armyworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    fut_seedling = SurveillanceRecord(
        observation_id="MAIZE-FUT-SEED",
        observation_date="2023-07-14",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="maize",
        pest_common_name="Fall Armyworm",
        pest_incidence_pct=7.0,
        crop_growth_stage="seedling",
        source_organization="TEST",
    )
    res_seedling = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_seedling],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res_seedling.outbreak_label_7d == 1
    assert res_seedling.label_status == "LABELED_OUTBREAK"
    assert "seedling" in res_seedling.notes

    fut_whorl = SurveillanceRecord(
        observation_id="MAIZE-FUT-WHORL",
        observation_date="2023-07-14",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="maize",
        pest_common_name="Fall Armyworm",
        pest_incidence_pct=7.0,
        crop_growth_stage="mid_whorl",
        source_organization="TEST",
    )
    res_whorl = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_whorl],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res_whorl.outbreak_label_7d == 0
    assert res_whorl.label_status == "LABELED_NON_OUTBREAK"


def test_severity_defoliation_threshold_triggers_outbreak():
    """
    Phase 14: Soybean tobacco caterpillar severity ETL is 20% defoliation.
    Even if incidence is sub-ETL (e.g. 10%), defoliation >= 20% triggers outbreak.
    """
    ref_rec = SurveillanceRecord(
        observation_id="SEV-REF-T0",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="soybean",
        pest_common_name="Tobacco Caterpillar",
        pest_incidence_pct=5.0,
        source_organization="TEST",
    )
    fut_sev = SurveillanceRecord(
        observation_id="SEV-FUT",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="soybean",
        pest_common_name="Tobacco Caterpillar",
        pest_incidence_pct=10.0,  # Below incidence ETL
        pest_severity_pct=25.0,   # Exceeds 20% defoliation ETL
        source_organization="TEST",
    )
    result = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_sev],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert result.outbreak_label_7d == 1
    assert result.label_status == "LABELED_OUTBREAK"
    assert "severity" in result.notes.lower()


def test_biological_mismatch_blocks_labeling():
    """
    Phase 14: Biologically incompatible crop-pest pairings (e.g. cotton with brown planthopper)
    are rejected by SurveillanceRecord validation, and compute_forward_outbreak_label
    returns label_status='BIOLOGICAL_MISMATCH' and outbreak_label_7d=None.
    """
    from unittest.mock import MagicMock

    # 1. Direct schema validation rejects the biological mismatch
    with pytest.raises(ValidationError):
        SurveillanceRecord(
            observation_id="MISMATCH-REF",
            observation_date="2023-08-01",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Brown Planthopper",  # Rice pest, cannot infest cotton
            pest_incidence_pct=25.0,
            source_organization="TEST",
        )

    # 2. Defense-in-depth: compute_forward_outbreak_label detects biological mismatch
    mock_rec = MagicMock(spec=SurveillanceRecord)
    mock_rec.observation_id = "MISMATCH-REF"
    mock_rec.observation_date = "2023-08-01"
    mock_rec.district = "Nagpur"
    mock_rec.crop = "cotton"
    mock_rec.pest_common_name = "Brown Planthopper"
    mock_rec.pest_incidence_pct = 25.0

    result = compute_forward_outbreak_label(
        record=mock_rec,
        longitudinal_surveillance_records=[mock_rec],
        forward_days=7,
    )
    assert result.outbreak_label_7d is None
    assert result.label_status == "BIOLOGICAL_MISMATCH"
    assert "Incompatible biological combination" in result.notes


def test_historical_transcription_pilot_quarantined_and_validated():
    """
    Phase 14: Reconciled historical research pilot data in quarantine
    must be cleanly parsable by load_surveillance_file, pass validation,
    carry dataset_classification='HISTORICAL_RESEARCH_TRIAL', and demonstrate
    proper longitudinal forward labeling behavior (including unobserved forward window).
    """
    quarantine_csv = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "raw"
        / "pest_surveillance"
        / "historical_transcriptions"
        / "reconciled_transcription.csv"
    )
    assert quarantine_csv.exists(), "Reconciled transcription pilot CSV must exist in quarantine."

    load_res = load_surveillance_file(quarantine_csv)
    assert load_res.total_raw_rows == 13
    assert len(load_res.loaded_records) == 13

    valid_records = [SurveillanceRecord(**d) for d in load_res.loaded_records]
    assert len(valid_records) == 13

    # All records must carry HISTORICAL_RESEARCH_TRIAL
    for r in valid_records:
        assert r.dataset_classification == "HISTORICAL_RESEARCH_TRIAL"
        assert r.source_organization == "DR_PDKV_AKOLA"
        assert r.crop == "cotton"
        assert r.pest_common_name == "Pink Bollworm"

    valid_surv_records, val_report = validate_surveillance_records(load_res.loaded_records)
    assert val_report.is_valid is True
    assert val_report.total_records == 13
    assert len(valid_surv_records) == 13

    # Test longitudinal labeling dynamics:
    # 1. SMW 32 (incidence 0.0%) -> SMW 33 (incidence 0.0%, severity 2.5%, sub-ETL): Label = 0
    rec_smw32 = next(r for r in valid_records if r.observation_id == "PDKV-2004-T7-SMW32")
    lbl_smw32 = compute_forward_outbreak_label(
        record=rec_smw32,
        longitudinal_surveillance_records=valid_records,
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert lbl_smw32.outbreak_label_7d == 0
    assert lbl_smw32.label_status == "LABELED_NON_OUTBREAK"

    # 2. SMW 36 -> SMW 37 was missing due to flood/rain: Label = None, status = UNOBSERVED_FUTURE_WINDOW
    rec_smw36 = next(r for r in valid_records if r.observation_id == "PDKV-2004-T7-SMW36")
    lbl_smw36 = compute_forward_outbreak_label(
        record=rec_smw36,
        longitudinal_surveillance_records=valid_records,
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert lbl_smw36.outbreak_label_7d is None
    assert lbl_smw36.label_status == "UNOBSERVED_FUTURE_WINDOW"

    # 3. SMW 38 -> SMW 39 damage is 12.5% (>= 10% ETL): Label = 1, status = LABELED_OUTBREAK
    rec_smw38 = next(r for r in valid_records if r.observation_id == "PDKV-2004-T7-SMW38")
    lbl_smw38 = compute_forward_outbreak_label(
        record=rec_smw38,
        longitudinal_surveillance_records=valid_records,
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert lbl_smw38.outbreak_label_7d == 1
    assert lbl_smw38.label_status == "LABELED_OUTBREAK"


# ══════════════════════════════════════════════════════════════════════════════
# 10. PHASE 15 — ADVANCED CONSECUTIVE TRAPS, DENSITIES & LEAKAGE BOUNDARY TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_consecutive_nights_trap_catch_outbreak():
    """
    Phase 15: Cotton Pink Bollworm requires 8-10 moths/trap/night for 3 consecutive nights.
    3 consecutive daily catches >= 8.0 must trigger LABELED_OUTBREAK.
    """
    ref_rec = SurveillanceRecord(
        observation_id="TRAP-REF-T0",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    d1 = SurveillanceRecord(
        observation_id="TRAP-D1",
        observation_date="2023-08-02",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        trap_catch_count=9.0,
        source_organization="TEST",
    )
    d2 = SurveillanceRecord(
        observation_id="TRAP-D2",
        observation_date="2023-08-03",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        trap_catch_count=8.5,
        source_organization="TEST",
    )
    d3 = SurveillanceRecord(
        observation_id="TRAP-D3",
        observation_date="2023-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        trap_catch_count=10.0,
        source_organization="TEST",
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, d1, d2, d3],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d == 1
    assert res.label_status == "LABELED_OUTBREAK"
    assert "consecutive" in res.notes.lower()


def test_consecutive_nights_trap_catch_broken_by_missing_day():
    """
    Phase 15: If 3 consecutive nights are required, a date gap (e.g. Day 1, Day 3, Day 4)
    does NOT satisfy 3 consecutive nights. If incidence is sub-ETL, trap catch alone
    must NOT trigger an outbreak.
    """
    ref_rec = SurveillanceRecord(
        observation_id="TRAP-GAP-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    # Day 1: 9.0 (exceeds 8.0)
    d1 = SurveillanceRecord(
        observation_id="TRAP-GAP-D1",
        observation_date="2023-08-02",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=1.0,
        trap_catch_count=9.0,
        source_organization="TEST",
    )
    # Day 2 is MISSING (scouting skipped)
    # Day 3: 9.5
    d3 = SurveillanceRecord(
        observation_id="TRAP-GAP-D3",
        observation_date="2023-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=1.0,
        trap_catch_count=9.5,
        source_organization="TEST",
    )
    # Day 4: 9.0 (Streak is only 2: Day 3 and Day 4; streak of 3 was broken by missing Day 2)
    d4 = SurveillanceRecord(
        observation_id="TRAP-GAP-D4",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=1.0,
        trap_catch_count=9.0,
        source_organization="TEST",
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, d1, d3, d4],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    # Does NOT reach 3 consecutive nights; incidence is sub-ETL -> 0
    assert res.outbreak_label_7d == 0
    assert res.label_status == "LABELED_NON_OUTBREAK"


def test_count_density_larvae_per_plant_exceeds_etl():
    """
    Phase 15: Cotton American Bollworm has density ETL of 1.0 larva/plant.
    Sampling 20 plants with 25 larvae (1.25 larvae/plant) triggers outbreak.
    """
    ref_rec = SurveillanceRecord(
        observation_id="DENS-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="American Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    fut_rec = SurveillanceRecord(
        observation_id="DENS-FUT",
        observation_date="2023-08-06",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="American Bollworm",
        pest_incidence_pct=3.0,   # Sub-ETL on % damage (ETL is 5%)
        plants_sampled=20,
        plants_affected=20,       # 20 affected plants / 20 sampled = 1.0 larva/plant >= 1.0 ETL
        crop_growth_stage="flowering",
        source_organization="TEST",
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d == 1
    assert res.label_status == "LABELED_OUTBREAK"
    assert "count density" in res.notes.lower()


def test_missing_growth_stage_falls_back_to_baseline_safely():
    """
    Phase 15: If crop_growth_stage is None/missing, system must safely fall back
    to baseline incidence ETL without crashing.
    """
    ref_rec = SurveillanceRecord(
        observation_id="NOSTAGE-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    fut_rec = SurveillanceRecord(
        observation_id="NOSTAGE-FUT",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=15.0,  # Exceeds baseline 10% ETL
        crop_growth_stage=None,   # Missing stage
        source_organization="TEST",
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d == 1
    assert res.label_status == "LABELED_OUTBREAK"
    assert "stage unspecified" in res.notes


def test_zero_future_to_past_leakage_strict_boundary():
    """
    Phase 15: Zero lookahead leakage verification.
    Observations on day T (same day) or past (t <= T) must NEVER be included
    in forward window [T+1, T+forward_days].
    """
    ref_rec = SurveillanceRecord(
        observation_id="LEAK-REF-T0",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    # Record on SAME DAY (T0) with massive incidence
    same_day_rec = SurveillanceRecord(
        observation_id="LEAK-SAME-DAY",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=50.0,
        source_organization="TEST",
    )
    # Record on PAST DAY (T-1) with massive incidence
    past_day_rec = SurveillanceRecord(
        observation_id="LEAK-PAST-DAY",
        observation_date="2023-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=50.0,
        source_organization="TEST",
    )

    # When no forward observations exist in [T+1, T+7], same-day and past records must NOT leak
    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, same_day_rec, past_day_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d is None
    assert res.label_status == "UNOBSERVED_FUTURE_WINDOW"
    assert res.observations_found_in_forward_window == 0


def test_single_night_trap_catch_does_not_satisfy_consecutive_nights_etl():
    """
    Phase 16 Safeguard: Pink Bollworm requires 3 consecutive nights >= 8.0 moths/night.
    An isolated single night with trap_catch=12.0 in the 7-day window does NOT satisfy
    the consecutive-night requirement and must NOT trigger an outbreak label.
    """
    ref_rec = SurveillanceRecord(
        observation_id="SINGLE-TRAP-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    single_trap_fut = SurveillanceRecord(
        observation_id="SINGLE-TRAP-FUT",
        observation_date="2023-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,     # Sub-ETL incidence
        trap_catch_count=12.0,      # High catch on single night (req=3 consecutive nights)
        source_organization="TEST",
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, single_trap_fut],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    # Does NOT satisfy 3 consecutive nights; incidence is sub-ETL -> verified non-outbreak
    assert res.outbreak_label_7d == 0
    assert res.label_status == "LABELED_NON_OUTBREAK"


def test_missing_measurements_in_forward_window_cannot_become_zero_label():
    """
    Phase 16 Safeguard: Surveillance records must not have all measurements missing.
    1. Schema validation strictly rejects a SurveillanceRecord with all None measurements.
    2. Even if constructed via model_construct, compute_forward_outbreak_label detects
       absence of quantitative measurements and returns label_status='MISSING_MEASUREMENTS'
       with outbreak_label_7d=None, preventing missing data from becoming a zero label.
    """
    import pytest
    from pydantic import ValidationError

    # 1. Verify schema rejects direct construction
    with pytest.raises(ValidationError, match="at least one quantitative measurement"):
        SurveillanceRecord(
            observation_id="NULL-MEAS-FUT",
            observation_date="2023-08-04",
            district="Nagpur",
            latitude=21.15,
            longitude=79.08,
            crop="cotton",
            pest_common_name="Pink Bollworm",
            pest_incidence_pct=None,
            trap_catch_count=None,
            pest_severity_pct=None,
            plants_affected=None,
            source_organization="TEST",
        )

    # 2. Verify compute_forward_outbreak_label safeguard
    ref_rec = SurveillanceRecord(
        observation_id="NULL-MEAS-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    unmeasured_fut = SurveillanceRecord.model_construct(
        observation_id="NULL-MEAS-FUT",
        observation_date="2023-08-04",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=None,
        trap_catch_count=None,
        pest_severity_pct=None,
        plants_affected=None,
        plants_sampled=None,
        crop_growth_stage=None,
        source_organization="TEST",
        taluka=None,
    )

    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, unmeasured_fut],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d is None
    assert res.label_status == "MISSING_MEASUREMENTS"
    assert "Missing measurements cannot be treated" in res.notes


def test_primary_source_retrieved_not_production_eligible():
    """
    Phase 16 Safeguard: PRIMARY_SOURCE_RETRIEVED thresholds are research-grade only.
    Even when evaluated in exploratory mode (require_fully_verified_etl=False),
    the resulting OutbreakLabelResult MUST carry production_eligible=False.
    Only formally expert-approved ('VERIFIED') thresholds can be production_eligible=True.
    """
    ref_rec = SurveillanceRecord(
        observation_id="PROD-ELIG-REF",
        observation_date="2023-08-01",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=2.0,
        source_organization="TEST",
    )
    fut_rec = SurveillanceRecord(
        observation_id="PROD-ELIG-FUT",
        observation_date="2023-08-05",
        district="Nagpur",
        latitude=21.15,
        longitude=79.08,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        pest_incidence_pct=25.0,  # Exceeds 10% ETL
        source_organization="TEST",
    )

    # In exploratory mode
    res = compute_forward_outbreak_label(
        record=ref_rec,
        longitudinal_surveillance_records=[ref_rec, fut_rec],
        forward_days=7,
        require_fully_verified_etl=False,
    )
    assert res.outbreak_label_7d == 1
    assert res.label_status == "LABELED_OUTBREAK"
    # Even though labeled 1 in research mode, it is strictly NOT production eligible!
    assert res.production_eligible is False




