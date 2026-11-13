"""
pest_surveillance_ingestion.py
──────────────────────────────
Interface and ingestion handler for authentic pest surveillance ground truth
(CROPSAP Maharashtra, ICAR-NCIPM, or localized agricultural research trap records).

Governed by strict scientific principles:
1. Never fabricates fake pest surveillance numbers.
2. Never silently replaces missing pest observations with zeros.
3. Honestly reports when departmental surveillance databases are access-restricted.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
DEFAULT_PEST_RAW_DIR = Path("data/raw/pest_surveillance")

EXPECTED_SURVEILLANCE_COLUMNS = [
    "observation_date",
    "district",
    "crop",
    "pest_type",
    "pest_incidence_pct",
    "pest_severity_pct",
    "trap_catch_count",
    "economic_threshold_exceeded",
    "source_agency",
]


@dataclass
class SurveillanceAuditResult:
    status: str
    available_files: list[str]
    total_records: int
    covered_districts: list[str]
    covered_crops: list[str]
    covered_pests: list[str]
    date_range: tuple[str, str] | None
    notes: str


def check_surveillance_data_availability(
    surveillance_dir: Path = DEFAULT_PEST_RAW_DIR,
) -> SurveillanceAuditResult:
    """
    Audit data/raw/pest_surveillance for authentic uploaded surveillance files.
    Returns status:
    - 'AVAILABLE' if valid real-world surveillance files exist.
    - 'AWAITING_GOVERNMENT_SURVEILLANCE_DATA' if directory is empty or only templates exist.
    """
    surveillance_dir.mkdir(parents=True, exist_ok=True)
    csv_files = list(surveillance_dir.glob("*.csv")) + list(surveillance_dir.glob("*.xlsx"))
    active_files = [f for f in csv_files if "template" not in f.name.lower()]

    if not active_files:
        msg = (
            "No authentic pest surveillance records found in data/raw/pest_surveillance/. "
            "CROPSAP Maharashtra and ICAR-NCIPM raw databases require government department credentials. "
            "Ingestion pipeline will operate in Environmental-Only (Tier 1) mode until authentic surveillance "
            "records are deposited."
        )
        LOGGER.warning(msg)
        return SurveillanceAuditResult(
            status="AWAITING_GOVERNMENT_SURVEILLANCE_DATA",
            available_files=[],
            total_records=0,
            covered_districts=[],
            covered_crops=[],
            covered_pests=[],
            date_range=None,
            notes=msg,
        )

    # Ingest and audit existing files
    dfs = []
    for f in active_files:
        try:
            if f.suffix == ".csv":
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f)
            dfs.append(df)
        except Exception as exc:
            LOGGER.error("Failed to read surveillance file %s: %s", f.name, exc)

    if not dfs:
        return SurveillanceAuditResult(
            status="CORRUPTED_FILES",
            available_files=[f.name for f in active_files],
            total_records=0,
            covered_districts=[],
            covered_crops=[],
            covered_pests=[],
            date_range=None,
            notes="Active surveillance files exist but could not be parsed.",
        )

    combined = pd.concat(dfs, ignore_index=True)
    districts = combined["district"].dropna().unique().tolist() if "district" in combined.columns else []
    crops = combined["crop"].dropna().unique().tolist() if "crop" in combined.columns else []
    pests = combined["pest_type"].dropna().unique().tolist() if "pest_type" in combined.columns else []

    date_range = None
    if "observation_date" in combined.columns:
        dates = pd.to_datetime(combined["observation_date"], errors="coerce").dropna()
        if not dates.empty:
            date_range = (dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d"))

    return SurveillanceAuditResult(
        status="AVAILABLE",
        available_files=[f.name for f in active_files],
        total_records=len(combined),
        covered_districts=districts,
        covered_crops=crops,
        covered_pests=pests,
        date_range=date_range,
        notes=f"Successfully identified {len(combined)} authentic surveillance records across {len(districts)} districts.",
    )


def load_pest_surveillance_data(
    surveillance_dir: Path = DEFAULT_PEST_RAW_DIR,
) -> pd.DataFrame:
    """
    Load and standardize available authentic surveillance records.
    Returns an empty DataFrame with the standard schema if no records exist.
    """
    surveillance_dir.mkdir(parents=True, exist_ok=True)
    audit = check_surveillance_data_availability(surveillance_dir)

    if audit.status != "AVAILABLE":
        LOGGER.info("Surveillance data not currently available (%s). Returning empty standardized frame.", audit.status)
        return pd.DataFrame(columns=EXPECTED_SURVEILLANCE_COLUMNS)

    dfs = []
    for fname in audit.available_files:
        fpath = surveillance_dir / fname
        if fpath.suffix == ".csv":
            df = pd.read_csv(fpath)
        else:
            df = pd.read_excel(fpath)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)

    # Standardize column mappings
    rename_map = {
        "date": "observation_date",
        "incidence": "pest_incidence_pct",
        "severity": "pest_severity_pct",
        "trap_catch": "trap_catch_count",
        "pest": "pest_type",
    }
    combined = combined.rename(columns=rename_map)

    # Ensure date format
    if "observation_date" in combined.columns:
        combined["observation_date"] = pd.to_datetime(combined["observation_date"])

    return combined


def create_surveillance_template(
    output_path: Path = DEFAULT_PEST_RAW_DIR / "cropsap_surveillance_template.csv",
) -> Path:
    """
    Generates a standardized CSV template for agricultural extension officers
    or researchers to deposit authentic CROPSAP/NCIPM field scouting records.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_template = pd.DataFrame([
        {
            "observation_date": "2023-07-15",
            "district": "Nagpur",
            "taluk": "Hingna",
            "village": "Kanhan",
            "latitude": 21.15,
            "longitude": 79.08,
            "crop": "Cotton",
            "growth_stage": "Squaring_bud",
            "pest_type": "Pink bollworm",
            "pest_incidence_pct": 8.5,
            "pest_severity_pct": 4.2,
            "trap_catch_count": 12,
            "economic_threshold_exceeded": 0,
            "source_agency": "CROPSAP-Maharashtra",
            "quality_flag": "AUTHENTIC_SCOUTED",
        },
        {
            "observation_date": "2023-07-22",
            "district": "Nagpur",
            "taluk": "Hingna",
            "village": "Kanhan",
            "latitude": 21.15,
            "longitude": 79.08,
            "crop": "Cotton",
            "growth_stage": "Flowering",
            "pest_type": "Pink bollworm",
            "pest_incidence_pct": 14.0,
            "pest_severity_pct": 11.5,
            "trap_catch_count": 28,
            "economic_threshold_exceeded": 1,
            "source_agency": "CROPSAP-Maharashtra",
            "quality_flag": "AUTHENTIC_SCOUTED",
        },
    ])
    df_template.to_csv(output_path, index=False)
    LOGGER.info("Created surveillance ingestion template at %s", output_path)
    return output_path

