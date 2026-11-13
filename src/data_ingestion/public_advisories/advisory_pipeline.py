"""
advisory_pipeline.py
────────────────────
End-to-end orchestration pipeline for public pest advisory ingestion,
provenance registration, extraction, validation, and structured persistence.

Executes:
1. Document discovery across local raw archive (data/raw/public_advisories/).
2. Provenance tracking with SHA-256 integrity verification.
3. Multilingual entity extraction (English, Marathi, Hindi).
4. Evidence classification into GENERAL_PREVENTIVE_ADVISORY, REPORTED_PEST_ACTIVITY,
   REPORTED_PEST_SEVERITY, or FIELD_SURVEILLANCE_MEASUREMENT.
5. Biological and geographic validation.
6. Persistence to data/processed/public_advisories/extracted_advisories.json.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from src.data_ingestion.public_advisories.advisory_discovery import (
    AdvisoryDiscoveryService,
    DEFAULT_RAW_ADVISORIES_DIR,
)
from src.data_ingestion.public_advisories.advisory_parser import (
    AdvisoryParser,
    ParsedAdvisoryDocument,
)
from src.data_ingestion.public_advisories.advisory_provenance import (
    AdvisoryProvenanceRegistry,
)
from src.data_ingestion.public_advisories.advisory_schema import (
    AdvisoryRecord,
)
from src.data_ingestion.public_advisories.advisory_sources import (
    get_advisory_source,
    list_advisory_sources,
)
from src.data_ingestion.public_advisories.advisory_validation import (
    AdvisoryValidationReport,
    AdvisoryValidator,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_PROCESSED_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "public_advisories"
)


class PublicAdvisoryIngestionPipeline:
    """Orchestrates end-to-end ingestion and processing of public pest advisories."""

    def __init__(
        self,
        raw_dir: Path | str = DEFAULT_RAW_ADVISORIES_DIR,
        processed_dir: Path | str = DEFAULT_PROCESSED_DIR,
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.provenance_registry = AdvisoryProvenanceRegistry(
            log_path=self.processed_dir / "advisory_provenance_log.json"
        )

    def run_pipeline(self) -> tuple[list[AdvisoryRecord], AdvisoryValidationReport]:
        """Run the complete discovery, extraction, validation, and storage pipeline."""
        discovered = AdvisoryDiscoveryService.scan_local_archive(self.raw_dir)
        all_records: list[AdvisoryRecord] = []

        LOGGER.info("Starting public advisory pipeline across %d discovered files", len(discovered))

        for item in discovered:
            file_path = Path(item.url_or_path)

            # Match source metadata
            source_info = get_advisory_source(item.source_id)
            org_name = source_info.organization_name if source_info else item.organization_name
            office = source_info.issuing_office if source_info else None
            source_url = source_info.portal_url if source_info else None

            # Register document in provenance log
            doc_entry, is_new = self.provenance_registry.register_document(
                source_id=item.source_id,
                file_path=file_path,
                publication_date=item.estimated_date,
                title=item.title,
            )

            # Parse document
            parsed_doc: ParsedAdvisoryDocument = AdvisoryParser.parse_file(
                file_path=file_path,
                source_id=item.source_id,
                issuing_organization=org_name,
                issuing_office=office,
                source_url=source_url,
                default_publication_date=item.estimated_date,
            )

            # Update provenance with record count
            self.provenance_registry.update_record_count(
                sha256_hash=doc_entry.sha256,
                count=len(parsed_doc.records),
                status="PROCESSED" if parsed_doc.success else "EXTRACTION_FAILED",
            )

            all_records.extend(parsed_doc.records)

        # Batch validation
        valid_records, val_report = AdvisoryValidator.validate_batch(all_records)

        # Save structured JSON
        output_file = self.processed_dir / "extracted_advisories.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in valid_records], f, indent=2, ensure_ascii=False)

        # Save validation report
        report_file = self.processed_dir / "advisory_validation_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(val_report.to_dict(), f, indent=2)

        LOGGER.info(
            "Advisory pipeline completed: %d total records extracted, %d valid, %d flagged",
            len(all_records), val_report.valid_records_count, val_report.flagged_records_count
        )
        return valid_records, val_report

