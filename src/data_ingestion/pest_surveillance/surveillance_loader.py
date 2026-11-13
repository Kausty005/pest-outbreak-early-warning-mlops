"""
surveillance_loader.py
──────────────────────
Ingestion and parsing module for authorized pest surveillance CSV and Excel files.

Features:
- Cryptographic SHA-256 provenance hashing of source files
- Flexible column alias mapping for state and university formats
- Dialect and encoding auto-detection (UTF-8, UTF-8-SIG, Latin-1)
- Strict preservation of missing values (no silent zero-imputation)
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.data_ingestion.pest_surveillance.surveillance_schema import SurveillanceRecord

LOGGER = logging.getLogger(__name__)

# Column name alias mappings from various agency formats
COLUMN_ALIASES: dict[str, str] = {
    "obs_id": "observation_id",
    "id": "observation_id",
    "record_id": "observation_id",
    "date": "observation_date",
    "survey_date": "observation_date",
    "scouting_date": "observation_date",
    "dist": "district",
    "district_name": "district",
    "taluk": "taluka",
    "tahsil": "taluka",
    "sub_district": "taluka",
    "lat": "latitude",
    "lon": "longitude",
    "lng": "longitude",
    "crop_name": "crop",
    "host_crop": "crop",
    "variety": "crop_variety",
    "hybrid": "crop_variety",
    "pest": "pest_common_name",
    "pest_name": "pest_common_name",
    "pest_type": "pest_common_name",
    "scientific_name": "pest_scientific_name",
    "incidence": "pest_incidence_pct",
    "incidence_pct": "pest_incidence_pct",
    "infestation_pct": "pest_incidence_pct",
    "severity": "pest_severity_pct",
    "severity_pct": "pest_severity_pct",
    "defoliation_pct": "pest_severity_pct",
    "trap_catch": "trap_catch_count",
    "moths_per_trap": "trap_catch_count",
    "moths_count": "trap_catch_count",
    "total_plants_sampled": "plants_sampled",
    "infested_plants": "plants_affected",
    "affected_plants": "plants_affected",
    "growth_stage": "crop_growth_stage",
    "stage": "crop_growth_stage",
    "sowing_dt": "sowing_date",
    "planting_date": "sowing_date",
    "dss": "days_since_sowing",
    "source_agency": "source_organization",
    "organization": "source_organization",
    "agency": "source_organization",
}


@dataclass
class LoadResult:
    """Result of loading a surveillance file."""
    source_path: Path
    file_sha256: str
    total_raw_rows: int
    loaded_records: list[dict[str, Any]]
    column_mapping_applied: dict[str, str]
    unmapped_columns: list[str]
    missing_mandatory_fields: list[str]
    errors: list[str] = field(default_factory=list)


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for provenance verification."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_surveillance_file(file_path: str | Path) -> LoadResult:
    """
    Load and normalize a surveillance export (CSV or Excel).

    Preserves source provenance and missing values strictly.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Surveillance file does not exist: {path}")

    file_hash = compute_file_sha256(path)

    # 1. Parse tabular data with encoding tolerance
    ext = path.suffix.lower()
    df: Optional[pd.DataFrame] = None
    if ext in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif ext == ".csv":
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue

    if df is None:
        raise ValueError(f"Could not read file {path} as CSV or Excel with supported encodings.")

    total_raw = len(df)
    if total_raw == 0:
        return LoadResult(
            source_path=path,
            file_sha256=file_hash,
            total_raw_rows=0,
            loaded_records=[],
            column_mapping_applied={},
            unmapped_columns=[],
            missing_mandatory_fields=["EMPTY_FILE"],
            errors=["File contains 0 records."],
        )

    # 2. Normalize Column Names via Aliases
    col_mapping: dict[str, str] = {}
    unmapped: list[str] = []
    normalized_cols: list[str] = []

    for c in df.columns:
        norm_key = str(c).strip().lower().replace(" ", "_").replace("-", "_")
        canonical = COLUMN_ALIASES.get(norm_key, norm_key)
        col_mapping[str(c)] = canonical
        normalized_cols.append(canonical)

    df.columns = normalized_cols

    # 3. Check Mandatory Identification Fields
    mandatory_fields = ["observation_date", "district", "latitude", "longitude", "crop", "pest_common_name"]
    missing_mandatory = [f for f in mandatory_fields if f not in df.columns]

    errors: list[str] = []
    if missing_mandatory:
        errors.append(f"Missing mandatory surveillance fields: {missing_mandatory}")

    # 4. Extract Records preserving NaNs as None
    # We replace NaN with None for dictionary representation
    records_dict: list[dict[str, Any]] = []
    if not missing_mandatory:
        for idx, row in df.iterrows():
            rec: dict[str, Any] = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    rec[col] = None
                else:
                    rec[col] = val
            # Ensure observation_id exists
            if "observation_id" not in rec or rec["observation_id"] is None:
                rec["observation_id"] = f"{path.stem}_{idx + 1}"
            # Ensure provenance default
            if "source_organization" not in rec or rec["source_organization"] is None:
                rec["source_organization"] = "UNSPECIFIED_SOURCE"
            rec["source_document"] = path.name

            records_dict.append(rec)

    return LoadResult(
        source_path=path,
        file_sha256=file_hash,
        total_raw_rows=total_raw,
        loaded_records=records_dict,
        column_mapping_applied=col_mapping,
        unmapped_columns=unmapped,
        missing_mandatory_fields=missing_mandatory,
        errors=errors,
    )

