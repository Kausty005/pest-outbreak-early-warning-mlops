"""
surveillance_validation.py
──────────────────────────
Rigorous data quality, physical bounds, duplicate detection, and
biological validity validation for raw pest surveillance records.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import pandas as pd

from src.data_ingestion.pest_surveillance.surveillance_schema import (
    MAHARASHTRA_BOUNDS,
    PHYSICAL_BOUNDS,
    VALID_CROP_PEST_COMBINATIONS,
    SurveillanceRecord,
    normalize_token,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class SurveillanceValidationReport:
    """Comprehensive data quality and physical integrity report for surveillance ingestion."""
    total_records: int
    valid_records_count: int
    invalid_records_count: int
    duplicate_count: int
    is_valid: bool
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    missing_value_counts: dict[str, int] = field(default_factory=dict)
    species_distribution: dict[str, int] = field(default_factory=dict)
    crop_distribution: dict[str, int] = field(default_factory=dict)
    district_distribution: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_surveillance_records(
    raw_records: list[dict[str, Any]],
) -> tuple[list[SurveillanceRecord], SurveillanceValidationReport]:
    """
    Validate a list of raw surveillance records.

    Returns:
        (validated_records, validation_report)
    """
    total = len(raw_records)
    if total == 0:
        return [], SurveillanceValidationReport(
            total_records=0,
            valid_records_count=0,
            invalid_records_count=0,
            duplicate_count=0,
            is_valid=False,
            failed_checks=["Empty record collection"],
        )

    valid_records: list[SurveillanceRecord] = []
    validation_errors: list[dict[str, Any]] = []
    seen_keys: set[tuple] = set()
    duplicate_count = 0

    missing_counts: dict[str, int] = {
        "pest_incidence_pct": 0,
        "pest_severity_pct": 0,
        "trap_catch_count": 0,
        "sowing_date": 0,
        "days_since_sowing": 0,
        "taluka": 0,
        "village": 0,
    }

    species_dist: dict[str, int] = {}
    crop_dist: dict[str, int] = {}
    district_dist: dict[str, int] = {}

    for idx, raw in enumerate(raw_records):
        obs_id = raw.get("observation_id", f"row_{idx}")

        # 1. Duplicate Detection
        key = (
            raw.get("observation_date"),
            normalize_token(raw.get("district")),
            normalize_token(raw.get("taluka")),
            normalize_token(raw.get("village")),
            normalize_token(raw.get("crop")),
            normalize_token(raw.get("pest_common_name")),
        )
        if key in seen_keys:
            duplicate_count += 1
            validation_errors.append({
                "index": idx,
                "observation_id": obs_id,
                "error_type": "DUPLICATE_RECORD",
                "message": f"Duplicate observation for {key}",
            })
            continue
        seen_keys.add(key)

        # 2. Track Missing Fields
        for fld in missing_counts:
            if raw.get(fld) is None:
                missing_counts[fld] += 1

        # 3. Validate against Pydantic SurveillanceRecord
        try:
            record = SurveillanceRecord(**raw)
            valid_records.append(record)

            # Track distributions
            c_norm = normalize_token(record.crop)
            p_norm = normalize_token(record.pest_common_name)
            d_norm = str(record.district).strip().capitalize()

            crop_dist[c_norm] = crop_dist.get(c_norm, 0) + 1
            species_dist[p_norm] = species_dist.get(p_norm, 0) + 1
            district_dist[d_norm] = district_dist.get(d_norm, 0) + 1

        except Exception as exc:
            validation_errors.append({
                "index": idx,
                "observation_id": obs_id,
                "error_type": "SCHEMA_VALIDATION_FAILURE",
                "message": str(exc),
            })

    passed_checks: list[str] = []
    failed_checks: list[str] = []

    if not validation_errors:
        passed_checks.append("All records comply with physical bounds and biological constraints")
    else:
        failed_checks.append(f"{len(validation_errors)} records failed schema or physical bounds checks")

    if duplicate_count == 0:
        passed_checks.append("No duplicate observations detected")
    else:
        failed_checks.append(f"{duplicate_count} duplicate observations detected")

    valid_count = len(valid_records)
    is_valid = valid_count > 0 and len(failed_checks) == 0

    report = SurveillanceValidationReport(
        total_records=total,
        valid_records_count=valid_count,
        invalid_records_count=len(validation_errors),
        duplicate_count=duplicate_count,
        is_valid=is_valid,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        validation_errors=validation_errors,
        missing_value_counts=missing_counts,
        species_distribution=species_dist,
        crop_distribution=crop_dist,
        district_distribution=district_dist,
    )

    return valid_records, report

