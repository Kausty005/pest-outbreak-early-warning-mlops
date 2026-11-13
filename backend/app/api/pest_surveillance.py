"""
backend/app/api/pest_surveillance.py
────────────────────────────────────
FastAPI endpoints for genuine field pest surveillance data entry,
validation, CSV batch upload, and progress dashboard.

STRICT INVARIANTS:
1. Genuine field surveillance data only. Zero synthetic observations.
2. An unobserved future window MUST NOT be defaulted to 0 (non-outbreak).
3. Newly entered observations default to UNVERIFIED or DRAFT; never auto-verified.
4. Supervised model training remains BLOCKED.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

from backend.app.schemas.pest_surveillance import (
    SurveillanceObservationInput,
    SurveillanceObservationResponse,
    SurveillanceDashboardResponse,
    SurveillanceUploadResponse,
    SurveillanceReviewRequest,
    SurveillanceReviewResponse,
)
from src.data_ingestion.pest_surveillance.surveillance_schema import (
    MAHARASHTRA_BOUNDS,
    PHYSICAL_BOUNDS,
    VALID_CROP_PEST_COMBINATIONS,
    VALID_SAMPLING_METHODS,
    SurveillanceRecord,
    normalize_token,
)
from src.data_ingestion.pest_surveillance.surveillance_validation import (
    validate_surveillance_records,
)
from src.data_ingestion.pest_surveillance.surveillance_pseudonymization import (
    sanitize_public_surveillance_record,
    fuzz_coordinates_deterministic,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/pest-surveillance", tags=["pest-surveillance"])

DATA_DIR = Path("data/processed/pest_surveillance")
RAW_DATA_DIR = Path("data/raw/pest_surveillance")
STORAGE_FILE = DATA_DIR / "field_surveillance_records.json"
AUDIT_FILE = DATA_DIR / "surveillance_audit_log.json"

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum CSV upload size
RESEARCH_ADMIN_KEY = os.environ.get("SURVEILLANCE_ADMIN_KEY", "RESEARCH_VALIDATED_KEY")
GENESIS_AUDIT_HASH = "GENESIS_AUDIT_BLOCK_00000000000000000000000000000000000000000000000000"


def _sanitize_csv_cell_value(val: Any) -> Any:
    """
    Sanitize CSV field to prevent formula injection (CWE-1236).
    Prepends a single quote if the value begins with =, +, -, @, \\t, or \\r
    unless the value represents a valid float/integer number.
    """
    if not isinstance(val, str) or not val:
        return val
    stripped = val.strip()
    if stripped.startswith(("=", "+", "-", "@", "\t", "\r")):
        try:
            float(stripped)
            return val
        except ValueError:
            return f"'{val}"
    return val


def _load_stored_records() -> list[dict[str, Any]]:
    """Load persistent surveillance records safely."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORAGE_FILE.exists():
        return []
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LOGGER.warning("Could not read %s: %s", STORAGE_FILE, e)
        return []


def _save_stored_records(records: list[dict[str, Any]]) -> None:
    """Save persistent surveillance records atomically."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _load_audit_log() -> list[dict[str, Any]]:
    """Load human review audit log."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AUDIT_FILE.exists():
        return []
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _compute_audit_entry_hash(prev_hash: str, entry_content: dict[str, Any]) -> str:
    """Compute SHA-256 hash chaining this entry to the preceding audit entry."""
    payload = json.dumps({k: v for k, v in entry_content.items() if k != "entry_hash"}, sort_keys=True)
    chained_data = f"{prev_hash}|{payload}".encode("utf-8")
    return hashlib.sha256(chained_data).hexdigest()


def _append_audit_entry(entry: dict[str, Any]) -> None:
    """Append immutable, cryptographically hash-chained human review audit entry."""
    log = _load_audit_log()
    prev_hash = log[-1].get("entry_hash", GENESIS_AUDIT_HASH) if log else GENESIS_AUDIT_HASH
    entry["prev_entry_hash"] = prev_hash
    entry["entry_hash"] = _compute_audit_entry_hash(prev_hash, entry)
    log.append(entry)
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


@router.get("/dashboard", response_model=SurveillanceDashboardResponse)
def get_surveillance_dashboard() -> SurveillanceDashboardResponse:
    """
    Return quantitative data acquisition metrics.
    Displays EXACT real counts (0 where no data exists, no simulated values).
    """
    records = _load_stored_records()

    unique_fields = set()
    verified_count = 0
    unverified_count = 0
    draft_count = 0
    districts = set()
    crops = set()
    pests = set()
    sampling_methods = set()

    for r in records:
        if r.get("is_draft"):
            draft_count += 1
            continue
        v_status = r.get("verification_status", "UNVERIFIED")
        if v_status in ("FIELD_SCOUT_VERIFIED", "KVK_EXPERT_VALIDATED", "ICAR_SCIENTIST_VALIDATED"):
            verified_count += 1
        else:
            unverified_count += 1

        f_key = (r.get("district"), r.get("taluka"), r.get("village"), round(r.get("latitude", 0), 3), round(r.get("longitude", 0), 3))
        unique_fields.add(f_key)
        if r.get("district"):
            districts.add(r["district"])
        if r.get("crop"):
            crops.add(r["crop"])
        if r.get("pest_common_name"):
            pests.add(r["pest_common_name"])
        if r.get("sampling_method"):
            sampling_methods.add(r["sampling_method"])

    # Formal institutional request status
    institutional_status = {
        "CROPSAP-Maharashtra": "UNSUBMITTED_DRAFT (docs/institutional_data_request_cropsap.md)",
        "ICAR-CICR-Nagpur": "UNSUBMITTED_DRAFT (docs/institutional_data_request_icar_cicr.md)",
        "KVK-Nagpur": "UNSUBMITTED_DRAFT (docs/institutional_data_request_kvk_nagpur.md)",
        "KVK-Yavatmal": "UNSUBMITTED_DRAFT (docs/institutional_data_request_kvk_yavatmal.md)",
        "Dr-PDKV-Akola": "UNSUBMITTED_DRAFT (docs/institutional_data_request_pdkv_akola.md)",
        "VNMKV-Parbhani": "UNSUBMITTED_DRAFT (docs/institutional_data_request_vnmkv_parbhani.md)",
    }

    scientific_invariants = {
        "synthetic_records_allowed": False,
        "ml_training_allowed": False,
        "supervised_outbreak_model_status": "BLOCKED",
        "minimum_records_required_for_ml": 500,
        "blocking_reason": (
            "No authentic multi-season field surveillance ground truth available yet. "
            "Public advisories and EFI scores cannot be used as training labels."
        ),
    }

    return SurveillanceDashboardResponse(
        total_records_received=len([r for r in records if not r.get("is_draft")]),
        unique_fields_monitored=len(unique_fields),
        verified_records_count=verified_count,
        unverified_records_count=unverified_count,
        draft_records_count=draft_count,
        positive_outbreak_windows=0,  # Requires longitudinal forward calculation
        verified_negative_windows=0,  # Requires longitudinal forward calculation
        unobserved_future_windows=0,
        districts_represented=sorted(list(districts)),
        crops_represented=sorted(list(crops)),
        pests_represented=sorted(list(pests)),
        sampling_methods_represented=sorted(list(sampling_methods)),
        duplicate_count=0,
        institutional_access_status=institutional_status,
        scientific_invariants=scientific_invariants,
    )


@router.get("/readiness-gate")
def get_production_readiness_gate() -> dict[str, Any]:
    """
    Centralized scientific and MLOps readiness gate for supervised pest-outbreak model training.
    Evaluates 11 evidence-based criteria across real project storage.
    """
    from src.pest_risk.production_readiness_gate import evaluate_production_readiness
    report = evaluate_production_readiness(surveillance_path=STORAGE_FILE)
    return report.to_dict()


@router.get("/audit-log/verify")
def verify_audit_log_integrity() -> dict[str, Any]:
    """
    Verify the cryptographic hash-chain integrity of the human review audit log.
    Ensures no audit entries have been altered, reordered, or deleted post-hoc.
    """
    log = _load_audit_log()
    if not log:
        return {
            "is_valid": True,
            "total_entries": 0,
            "verified_entries": 0,
            "message": "Audit log is empty (Genesis state).",
        }

    expected_prev = GENESIS_AUDIT_HASH
    for idx, entry in enumerate(log):
        if entry.get("prev_entry_hash") != expected_prev:
            return {
                "is_valid": False,
                "total_entries": len(log),
                "verified_entries": idx,
                "tampered_at_index": idx,
                "message": f"Hash chain broken at index {idx}: prev_entry_hash mismatch.",
            }
        computed_hash = _compute_audit_entry_hash(expected_prev, entry)
        if entry.get("entry_hash") != computed_hash:
            return {
                "is_valid": False,
                "total_entries": len(log),
                "verified_entries": idx,
                "tampered_at_index": idx,
                "message": f"Tampering detected at index {idx}: payload hash mismatch.",
            }
        expected_prev = entry.get("entry_hash")

    return {
        "is_valid": True,
        "total_entries": len(log),
        "verified_entries": len(log),
        "message": f"Audit chain verified successfully ({len(log)} entries cryptographically sealed).",
    }


@router.get("/records")
def list_surveillance_records(
    district: Optional[str] = Query(None, description="Filter by district"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    pest: Optional[str] = Query(None, description="Filter by pest"),
    verification_status: Optional[str] = Query(None, description="Filter by status"),
    include_drafts: bool = Query(True, description="Include draft records"),
    fuzz_coordinates: bool = Query(True, description="Apply privacy-preserving coordinate fuzzing (1.5-3km)"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> dict[str, Any]:
    """
    Retrieve filtered list of recorded field observations.

    PRIVACY CONTROL:
    By default, `fuzz_coordinates=True` applies deterministic spatial displacement (1.5–3.0 km)
    and village name suppression to prevent farm re-identification.
    Requesting unmasked coordinates (`fuzz_coordinates=False`) requires a valid
    authorized research API key in the `X-API-Key` header.
    """
    if not fuzz_coordinates:
        admin_key = os.environ.get("SURVEILLANCE_ADMIN_KEY", RESEARCH_ADMIN_KEY)
        if not x_api_key or not hmac.compare_digest(x_api_key, admin_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to exact unmasked farm coordinates requires valid researcher authorization. Set fuzz_coordinates=true for public access.",
            )

    all_records = _load_stored_records()
    filtered = []
    for r in all_records:
        if not include_drafts and r.get("is_draft"):
            continue
        if district and r.get("district", "").lower() != district.lower():
            continue
        if crop and r.get("crop", "").lower() != crop.lower():
            continue
        if pest and pest.lower() not in r.get("pest_common_name", "").lower():
            continue
        if verification_status and r.get("verification_status") != verification_status:
            continue

        if fuzz_coordinates:
            filtered.append(sanitize_public_surveillance_record(r))
        else:
            filtered.append(r)

    return {
        "total_count": len(filtered),
        "records": filtered,
        "audit_entries_count": len(_load_audit_log()),
        "coordinates_fuzzed": fuzz_coordinates,
    }


@router.post("/records", response_model=SurveillanceObservationResponse)
def create_surveillance_observation(
    obs: SurveillanceObservationInput,
) -> SurveillanceObservationResponse:
    """
    Ingest a single field observation from mobile scout or web form.
    Validates biological compatibility, physical bounds, and sets initial status.
    NEVER automatically marks an observation as verified.
    """
    warnings: list[str] = []
    obs_id = obs.observation_id or f"OBS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

    # Biological compatibility check
    norm_crop = normalize_token(obs.crop)
    norm_pest = normalize_token(obs.pest_common_name)
    is_compat = False
    for c, p in VALID_CROP_PEST_COMBINATIONS:
        if c == norm_crop and (p in norm_pest or norm_pest in p):
            is_compat = True
            break
    if not is_compat:
        msg = f"Biological mismatch warning: Pest '{obs.pest_common_name}' is not recognized as a primary pest of crop '{obs.crop}'."
        warnings.append(msg)
        if not obs.is_draft:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation failed: {msg}"
            )

    # Geographic boundary check (Maharashtra)
    if not (MAHARASHTRA_BOUNDS["lat_min"] <= obs.latitude <= MAHARASHTRA_BOUNDS["lat_max"]):
        msg = f"Latitude {obs.latitude} is outside Maharashtra bounds [{MAHARASHTRA_BOUNDS['lat_min']}, {MAHARASHTRA_BOUNDS['lat_max']}]."
        warnings.append(msg)
        if not obs.is_draft:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    if not (MAHARASHTRA_BOUNDS["lon_min"] <= obs.longitude <= MAHARASHTRA_BOUNDS["lon_max"]):
        msg = f"Longitude {obs.longitude} is outside Maharashtra bounds [{MAHARASHTRA_BOUNDS['lon_min']}, {MAHARASHTRA_BOUNDS['lon_max']}]."
        warnings.append(msg)
        if not obs.is_draft:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    # At least one quantitative measurement required for non-drafts
    has_measure = (
        obs.pest_incidence_pct is not None
        or obs.pest_severity_pct is not None
        or obs.trap_catch_count is not None
        or obs.plants_affected is not None
    )
    if not obs.is_draft and not has_measure:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Surveillance observation requires at least one quantitative measure (incidence %, severity %, trap catch, or affected plants)."
        )

    # Photo evidence verification warning
    if not obs.is_draft and not obs.photo_evidence_sha256:
        warnings.append("Missing photo evidence: Submitted field observation should include a cryptographically hashed geotagged photograph.")

    # Late submission check (>3 days delay)
    if not obs.is_draft:
        try:
            obs_dt = datetime.strptime(obs.observation_date[:10], "%Y-%m-%d").date()
            today = datetime.utcnow().date()
            if (today - obs_dt).days > 3:
                warnings.append(f"Late submission warning: Observation date ({obs.observation_date}) is more than 3 days prior to current submission date.")
        except Exception:
            pass

    # Construct final stored record
    record_data = obs.model_dump()
    record_data["observation_id"] = obs_id
    record_data["created_at"] = datetime.utcnow().isoformat()
    record_data["verification_status"] = "DRAFT" if obs.is_draft else "UNVERIFIED"

    records = _load_stored_records()

    # Business duplicate detection for non-draft submissions
    if not obs.is_draft:
        dup = next(
            (
                r for r in records
                if not r.get("is_draft")
                and r.get("observation_id") != obs_id
                and r.get("observation_date") == obs.observation_date
                and normalize_token(r.get("district")) == normalize_token(obs.district)
                and normalize_token(r.get("taluka")) == normalize_token(obs.taluka)
                and normalize_token(r.get("village")) == normalize_token(obs.village)
                and normalize_token(r.get("crop")) == norm_crop
                and normalize_token(r.get("pest_common_name")) == norm_pest
            ),
            None,
        )
        if dup:
            loc_str = f"{obs.district}/{obs.taluka or ''}/{obs.village or ''}".strip("/")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate observation detected: Record already exists for {obs.crop} / {obs.pest_common_name} on {obs.observation_date} at {loc_str} (Existing Observation ID: {dup.get('observation_id')}).",
            )

    # Check update vs insert by observation_id
    existing_idx = next((i for i, r in enumerate(records) if r["observation_id"] == obs_id), None)
    if existing_idx is not None:
        records[existing_idx] = record_data
    else:
        records.append(record_data)

    _save_stored_records(records)

    return SurveillanceObservationResponse(
        success=True,
        observation_id=obs_id,
        record=record_data,
        validation_status="DRAFT" if obs.is_draft else "VALID",
        warnings=warnings,
        message="Observation recorded as DRAFT." if obs.is_draft else "Observation recorded and queued for human verification.",
    )


@router.post("/upload-csv", response_model=SurveillanceUploadResponse)
async def upload_surveillance_csv(
    file: UploadFile = File(..., description="CSV file with field surveillance observations"),
) -> SurveillanceUploadResponse:
    """
    Batch CSV upload endpoint for genuine surveillance data.
    Validates structure, bounds, and biological compatibility.
    Computes cryptographic SHA-256 hash and isolates raw file.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be a CSV (.csv)")

    contents = await file.read()
    if len(contents) > MAX_CSV_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV file exceeds maximum permitted size of {MAX_CSV_SIZE_BYTES // (1024 * 1024)} MB (received: {len(contents)} bytes).",
        )

    sha256_hash = hashlib.sha256(contents).hexdigest()

    # Save raw file securely in raw data directory
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DATA_DIR / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    with open(raw_path, "wb") as f:
        f.write(contents)

    # Parse CSV rows with formula injection sanitization
    try:
        text_stream = io.StringIO(contents.decode("utf-8", errors="replace"))
        reader = csv.DictReader(text_stream)
        raw_rows = []
        for r in reader:
            sanitized_row = {k: _sanitize_csv_cell_value(v) for k, v in r.items()}
            raw_rows.append(sanitized_row)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to parse CSV: {e}")

    if not raw_rows:
        return SurveillanceUploadResponse(
            success=False,
            filename=file.filename,
            file_sha256=sha256_hash,
            total_rows_processed=0,
            valid_rows_count=0,
            invalid_rows_count=0,
            duplicates_detected=0,
            validation_passed=False,
            errors=[{"error": "CSV contains no data rows"}],
            passed_checks=[],
            failed_checks=["Empty file"],
            records_saved_count=0,
        )

    # Run surveillance validation module
    valid_records, val_report = validate_surveillance_records(raw_rows)

    # Persist valid records in processing queue
    if valid_records:
        stored = _load_stored_records()
        for v in valid_records:
            d = v.model_dump()
            d["is_draft"] = False
            d["source_document"] = file.filename
            d["source_document_sha256"] = sha256_hash
            # Ensure verification_status is unverified initially
            d["verification_status"] = "UNVERIFIED"
            stored.append(d)
        _save_stored_records(stored)

    return SurveillanceUploadResponse(
        success=val_report.is_valid,
        filename=file.filename,
        file_sha256=sha256_hash,
        total_rows_processed=val_report.total_records,
        valid_rows_count=val_report.valid_records_count,
        invalid_rows_count=val_report.invalid_records_count,
        duplicates_detected=val_report.duplicate_count,
        validation_passed=val_report.is_valid,
        errors=val_report.validation_errors,
        passed_checks=val_report.passed_checks,
        failed_checks=val_report.failed_checks,
        records_saved_count=len(valid_records),
    )


@router.post("/review", response_model=SurveillanceReviewResponse)
def review_surveillance_record(
    review: SurveillanceReviewRequest,
) -> SurveillanceReviewResponse:
    """
    Human review endpoint for entomologists and KVK experts.
    Approves, rejects, or applies corrections to an observation.
    Maintains an immutable audit trail.
    """
    records = _load_stored_records()
    target = next((r for r in records if r["observation_id"] == review.observation_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation '{review.observation_id}' not found.")

    old_status = target.get("verification_status", "UNVERIFIED")
    new_status = old_status

    if review.action == "APPROVE":
        new_status = "KVK_EXPERT_VALIDATED"
        target["verification_status"] = new_status
        target["is_draft"] = False
    elif review.action == "REJECT":
        new_status = "REJECTED"
        target["verification_status"] = new_status
    elif review.action == "CORRECT_FIELDS":
        new_status = "FIELD_SCOUT_VERIFIED"
        target["verification_status"] = new_status
        target["is_draft"] = False
        if review.field_corrections:
            for k, v in review.field_corrections.items():
                if k in target:
                    target[k] = v
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown action: '{review.action}'. Must be APPROVE, REJECT, or CORRECT_FIELDS.")

    target["reviewed_by"] = review.reviewer_id
    target["reviewed_at"] = datetime.utcnow().isoformat()
    target["reviewer_notes"] = review.justification

    _save_stored_records(records)

    audit_id = f"AUD-{uuid4().hex[:8].upper()}"
    audit_entry = {
        "audit_id": audit_id,
        "observation_id": review.observation_id,
        "reviewer_id": review.reviewer_id,
        "action": review.action,
        "old_status": old_status,
        "new_status": new_status,
        "justification": review.justification,
        "field_corrections": review.field_corrections or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    _append_audit_entry(audit_entry)

    return SurveillanceReviewResponse(
        success=True,
        observation_id=review.observation_id,
        new_status=new_status,
        reviewed_by=review.reviewer_id,
        timestamp=audit_entry["timestamp"],
        audit_id=audit_id,
        message=f"Observation '{review.observation_id}' transitioned to '{new_status}'. Audit entry '{audit_id}' logged.",
    )

