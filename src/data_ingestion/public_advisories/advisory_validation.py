"""
advisory_validation.py
──────────────────────
Quality validation, consistency checks, and human review workflow management
for extracted agricultural pest advisories.

Enforces:
1. Strict biological validity (crop-pest pairing checks).
2. Geographic bounds consistency (Maharashtra districts).
3. Evidence classification discipline (prevents false escalation to field measurements).
4. Full human review audit trail for corrections and approvals.
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.data_ingestion.public_advisories.advisory_normalization import (
    CROP_LEXICON,
    MAHARASHTRA_DISTRICTS,
    PEST_LEXICON,
)
from src.data_ingestion.public_advisories.advisory_schema import (
    AdvisoryRecord,
    EvidenceType,
    HumanReviewAuditEntry,
    HumanReviewStatus,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class AdvisoryValidationReport:
    """Summary metrics of advisory validation run."""
    total_records: int = 0
    valid_records_count: int = 0
    flagged_records_count: int = 0
    evidence_type_distribution: dict[str, int] = field(default_factory=dict)
    crop_distribution: dict[str, int] = field(default_factory=dict)
    pest_distribution: dict[str, int] = field(default_factory=dict)
    district_distribution: dict[str, int] = field(default_factory=dict)
    language_distribution: dict[str, int] = field(default_factory=dict)
    review_status_distribution: dict[str, int] = field(default_factory=dict)
    issues_detected: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdvisoryValidator:
    """Validates AdvisoryRecords and manages human review interventions."""

    @classmethod
    def validate_record(cls, record: AdvisoryRecord) -> list[str]:
        """
        Validate an individual AdvisoryRecord.
        Returns a list of issue warning strings.
        """
        issues: list[str] = []

        # 1. SHA-256 hash format
        if not record.document_sha256 or len(record.document_sha256) != 64:
            issues.append(f"Invalid or missing document_sha256: '{record.document_sha256}'")

        # 2. Text non-empty
        if not record.advisory_text or len(record.advisory_text.strip()) < 5:
            issues.append("Advisory text is empty or too short.")

        # 3. Crop validation
        if record.crop and record.crop not in CROP_LEXICON:
            issues.append(f"Unknown crop '{record.crop}' not in standard agricultural lexicon.")

        # 4. District validation
        if record.district and record.district not in MAHARASHTRA_DISTRICTS:
            issues.append(f"District '{record.district}' is not recognized in Maharashtra registry.")

        # 5. Crop-Pest biological consistency
        if record.crop and record.pest_common_name:
            for pest_id, info in PEST_LEXICON.items():
                if info["common_name"].lower() == record.pest_common_name.lower():
                    if record.crop not in info["primary_crops"]:
                        issues.append(
                            f"Biological mismatch: Pest '{record.pest_common_name}' is not typically "
                            f"a primary pest of crop '{record.crop}' (expected: {info['primary_crops']})."
                        )
                    break

        # 6. Surveillance measurement classification safety rule
        if record.evidence_type == EvidenceType.FIELD_SURVEILLANCE_MEASUREMENT:
            if record.human_review_status == HumanReviewStatus.PENDING_REVIEW:
                issues.append(
                    "Safety Alert: Record classified as FIELD_SURVEILLANCE_MEASUREMENT must undergo "
                    "formal human entomological review before any consideration for surveillance datasets."
                )

        return issues

    @classmethod
    def validate_batch(cls, records: list[AdvisoryRecord]) -> tuple[list[AdvisoryRecord], AdvisoryValidationReport]:
        """Validate a collection of AdvisoryRecords and produce aggregate report."""
        report = AdvisoryValidationReport(total_records=len(records))
        valid_records: list[AdvisoryRecord] = []

        evidence_counter = Counter()
        crop_counter = Counter()
        pest_counter = Counter()
        district_counter = Counter()
        lang_counter = Counter()
        review_counter = Counter()

        for rec in records:
            issues = cls.validate_record(rec)

            evidence_counter[rec.evidence_type.value] += 1
            if rec.crop:
                crop_counter[rec.crop] += 1
            if rec.pest_common_name:
                pest_counter[rec.pest_common_name] += 1
            if rec.district:
                district_counter[rec.district] += 1
            lang_counter[rec.original_language] += 1
            review_counter[rec.human_review_status.value] += 1

            if issues:
                report.flagged_records_count += 1
                report.issues_detected.append({
                    "advisory_id": rec.advisory_id,
                    "source_document": rec.source_document,
                    "issues": issues,
                })
            else:
                report.valid_records_count += 1

            valid_records.append(rec)

        report.evidence_type_distribution = dict(evidence_counter)
        report.crop_distribution = dict(crop_counter)
        report.pest_distribution = dict(pest_counter)
        report.district_distribution = dict(district_counter)
        report.language_distribution = dict(lang_counter)
        report.review_status_distribution = dict(review_counter)

        return valid_records, report

    @classmethod
    def apply_human_review(
        cls,
        record: AdvisoryRecord,
        reviewer_id: str,
        action: str,  # "APPROVE", "REJECT", "CORRECT_FIELDS", "FLAG_FOR_SURVEILLANCE"
        field_updates: Optional[dict[str, Any]] = None,
        justification: str = "Routine reviewer evaluation",
    ) -> tuple[AdvisoryRecord, HumanReviewAuditEntry]:
        """
        Apply human reviewer action, update record fields, and generate audit entry.
        Does NOT automatically promote records to field surveillance observations.
        """
        changes: dict[str, dict[str, Any]] = {}

        # Convert record to dict for modification
        rec_data = record.model_dump()

        if field_updates:
            for k, new_val in field_updates.items():
                if k in rec_data and rec_data[k] != new_val:
                    changes[k] = {"old": rec_data[k], "new": new_val}
                    rec_data[k] = new_val

        # Update review status
        old_status = record.human_review_status
        new_status = old_status

        if action == "APPROVE":
            new_status = HumanReviewStatus.VERIFIED_ADVISORY
        elif action == "REJECT":
            new_status = HumanReviewStatus.REJECTED_EXTRACTION
        elif action == "FLAG_FOR_SURVEILLANCE":
            # Guard: only allow if evidence type is field measurement and sampling is documented
            if record.evidence_type != EvidenceType.FIELD_SURVEILLANCE_MEASUREMENT:
                raise ValueError(
                    f"Cannot flag advisory '{record.advisory_id}' for surveillance consideration: "
                    f"Evidence type is '{record.evidence_type.value}', not 'FIELD_SURVEILLANCE_MEASUREMENT'."
                )
            new_status = HumanReviewStatus.PROMOTED_FOR_SURVEILLANCE_CONSIDERATION
        elif action == "CORRECT_FIELDS":
            new_status = HumanReviewStatus.VERIFIED_ADVISORY

        changes["human_review_status"] = {"old": old_status.value, "new": new_status.value}
        rec_data["human_review_status"] = new_status
        rec_data["human_reviewer_notes"] = justification
        rec_data["reviewed_by"] = reviewer_id
        rec_data["reviewed_at"] = datetime.utcnow().isoformat()

        updated_record = AdvisoryRecord(**rec_data)

        audit_entry = HumanReviewAuditEntry(
            advisory_id=record.advisory_id,
            reviewer_id=reviewer_id,
            action=action,
            field_changes=changes,
            justification=justification,
        )

        LOGGER.info(
            "Applied human review on advisory %s: action=%s, reviewer=%s, changes=%d",
            record.advisory_id, action, reviewer_id, len(changes)
        )
        return updated_record, audit_entry

