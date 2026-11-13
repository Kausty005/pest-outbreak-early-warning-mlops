"""
advisory_discovery.py
─────────────────────
Discovery service for publicly accessible agricultural pest advisories.

Scans:
1. Official public portal indexes (CROPSAP, ICAR-CICR, IMD Agrimet, PDKV, KVK).
2. Local raw archive directories (data/raw/public_advisories/).
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from src.data_ingestion.public_advisories.advisory_sources import (
    AdvisorySourceInfo,
    list_advisory_sources,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_RAW_ADVISORIES_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "public_advisories"
)


@dataclass
class DiscoveredAdvisoryItem:
    """Discovered bulletin metadata prior to ingestion."""
    item_id: str
    source_id: str
    organization_name: str
    title: str
    format: str  # "PDF", "HTML", "TXT"
    target_crops: list[str]
    target_districts: list[str]
    estimated_date: Optional[str]
    url_or_path: str
    is_local: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdvisoryDiscoveryService:
    """Discovers available advisory bulletins from approved public sources and local archives."""

    @classmethod
    def scan_local_archive(
        cls,
        archive_dir: Path | str = DEFAULT_RAW_ADVISORIES_DIR,
    ) -> list[DiscoveredAdvisoryItem]:
        """Scan local archive folder for stored advisory documents."""
        directory = Path(archive_dir)
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            return []

        discovered: list[DiscoveredAdvisoryItem] = []
        for file_path in directory.glob("*.*"):
            suffix = file_path.suffix.lower()
            if suffix not in [".pdf", ".html", ".htm", ".txt"]:
                continue

            fmt = suffix.replace(".", "").upper()
            stem = file_path.stem

            # Match source ID from filename tokens (e.g. cicr, cropsap, imd, pdkv)
            source_id = "UNKNOWN-PUBLIC"
            stem_lower = stem.lower()
            for src in list_advisory_sources():
                tokens = [t.lower() for t in src.source_id.split("-") if len(t) > 2]
                if any(t in stem_lower for t in tokens):
                    source_id = src.source_id
                    break

            item = DiscoveredAdvisoryItem(
                item_id=f"DISC-LOCAL-{stem[:12]}",
                source_id=source_id,
                organization_name="Local Archive Storage",
                title=stem.replace("_", " ").title(),
                format=fmt,
                target_crops=["cotton", "soybean"],
                target_districts=["Nagpur", "Amravati", "Yavatmal", "Jalgaon"],
                estimated_date=None,
                url_or_path=str(file_path.resolve()),
                is_local=True,
            )
            discovered.append(item)

        LOGGER.info("Discovered %d local advisory files in %s", len(discovered), directory)
        return discovered

    @classmethod
    def list_curated_historical_bulletins(cls) -> list[DiscoveredAdvisoryItem]:
        """
        Return the catalog of known public seasonal bulletins for Maharashtra Vidarbha/Khandesh.
        Enables reproducible offline pipeline testing and analysis.
        """
        return [
            DiscoveredAdvisoryItem(
                item_id="DISC-CICR-2023-W28",
                source_id="ICAR-CICR-PUB",
                organization_name="ICAR-Central Institute for Cotton Research, Nagpur",
                title="Weekly Cotton Advisory Bulletin - Vidarbha Zone SMW 28 (July 2023)",
                format="PDF",
                target_crops=["cotton"],
                target_districts=["Nagpur", "Wardha", "Amravati", "Yavatmal"],
                estimated_date="2023-07-11",
                url_or_path="https://cicr.icar.gov.in/weekly-advisory/2023_07_11_vidarbha.pdf",
                is_local=False,
            ),
            DiscoveredAdvisoryItem(
                item_id="DISC-CROPSAP-2023-B04",
                source_id="CROPSAP-PUBLIC",
                organization_name="Department of Agriculture, Maharashtra (CROPSAP)",
                title="Pik Sanrakshan Salla Bulletin 4 - Pink Bollworm & Spodoptera Alert (Aug 2023)",
                format="PDF",
                target_crops=["cotton", "soybean"],
                target_districts=["Nagpur", "Amravati", "Yavatmal", "Jalgaon"],
                estimated_date="2023-08-08",
                url_or_path="https://cropsap.maharashtra.gov.in/bulletins/2023_aug_salla_04.pdf",
                is_local=False,
            ),
            DiscoveredAdvisoryItem(
                item_id="DISC-IMD-AAS-NGP-2023-66",
                source_id="IMD-AGROMET",
                organization_name="IMD Agrimet Pune & Dr. PDKV Regional Centre",
                title="District Agromet Advisory Bulletin for Nagpur District (18 Aug 2023)",
                format="PDF",
                target_crops=["cotton", "soybean", "rice"],
                target_districts=["Nagpur"],
                estimated_date="2023-08-18",
                url_or_path="https://imdagrimet.gov.in/bulletin/nagpur_20230818.pdf",
                is_local=False,
            ),
            DiscoveredAdvisoryItem(
                item_id="DISC-PDKV-2023-MR-09",
                source_id="PDKV-AKOLA",
                organization_name="Dr. PDKV Akola Extension Directorate",
                title="विदर्भ विभाग कापूस व सोयाबीन पीक संरक्षण सल्ला (सप्टेंबर २०२३)",
                format="PDF",
                target_crops=["cotton", "soybean"],
                target_districts=["Akola", "Amravati", "Yavatmal", "Buldhana"],
                estimated_date="2023-09-05",
                url_or_path="https://www.pdkv.ac.in/advisories/pdkv_salla_sep_2023.pdf",
                is_local=False,
            ),
        ]

