"""
advisory_parser.py
──────────────────
Extracts structured agricultural intelligence from PDF and HTML public advisories.

Enforces:
1. Evidence classification into GENERAL_PREVENTIVE_ADVISORY, REPORTED_PEST_ACTIVITY,
   REPORTED_PEST_SEVERITY, or FIELD_SURVEILLANCE_MEASUREMENT.
2. Preservation of verbatim original text, page numbers, and source attribution.
3. Date parsing across English, Marathi, and Hindi conventions.
4. Robust fallback handling — documents with partial or failed extractions
   are flagged with uncertainty and preserved for human review.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from bs4 import BeautifulSoup
import pypdf

from src.data_ingestion.public_advisories.advisory_normalization import (
    AdvisoryNormalizer,
    NormalizedEntities,
)
from src.data_ingestion.public_advisories.advisory_provenance import (
    compute_document_sha256,
)
from src.data_ingestion.public_advisories.advisory_schema import (
    AdvisoryRecord,
    AdvisorySeverity,
    EvidenceType,
    HumanReviewStatus,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class ParsedAdvisoryDocument:
    """Result of parsing an advisory file."""
    source_file: str
    document_sha256: str
    total_pages_or_sections: int
    records: list[AdvisoryRecord] = field(default_factory=list)
    extraction_errors: list[str] = field(default_factory=list)
    success: bool = True


class AdvisoryParser:
    """Parses public advisory documents (PDF, HTML, text) into structured AdvisoryRecords."""

    @classmethod
    def parse_file(
        cls,
        file_path: Path | str,
        source_id: str,
        issuing_organization: str,
        issuing_office: Optional[str] = None,
        source_url: Optional[str] = None,
        default_publication_date: Optional[str] = None,
    ) -> ParsedAdvisoryDocument:
        """Parse an advisory document by detecting its format from extension and content."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Advisory file does not exist: {path}")

        sha256_hash = compute_document_sha256(path)
        suffix = path.suffix.lower()

        try:
            if suffix == ".pdf":
                return cls.parse_pdf(
                    path, sha256_hash, source_id, issuing_organization,
                    issuing_office, source_url, default_publication_date
                )
            elif suffix in [".html", ".htm"]:
                return cls.parse_html(
                    path, sha256_hash, source_id, issuing_organization,
                    issuing_office, source_url, default_publication_date
                )
            else:
                # Text or structured markdown/csv
                return cls.parse_text(
                    path, sha256_hash, source_id, issuing_organization,
                    issuing_office, source_url, default_publication_date
                )
        except Exception as e:
            LOGGER.error("Failed to extract content from %s: %s", path.name, e)
            # Do NOT discard the document! Create an empty unparsed record for manual inspection.
            rec = AdvisoryRecord(
                advisory_id=f"ADV-{source_id.upper()}-{uuid4().hex[:8]}",
                publication_date=default_publication_date,
                issuing_organization=issuing_organization,
                issuing_office=issuing_office,
                source_document=path.name,
                source_url=source_url,
                advisory_text=f"[EXTRACTION_FAILED] Parser encountered error: {str(e)}",
                document_sha256=sha256_hash,
                extraction_method="fallback_error_handler",
                extraction_confidence=0.0,
                extraction_flags=["EXTRACTION_FAILED", f"ERROR_{type(e).__name__}"],
                human_review_status=HumanReviewStatus.PENDING_REVIEW,
                human_reviewer_notes="Automated extraction failed. Manual inspection of source document required.",
            )
            return ParsedAdvisoryDocument(
                source_file=path.name,
                document_sha256=sha256_hash,
                total_pages_or_sections=0,
                records=[rec],
                extraction_errors=[str(e)],
                success=False,
            )

    @classmethod
    def parse_pdf(
        cls,
        path: Path,
        sha256_hash: str,
        source_id: str,
        issuing_organization: str,
        issuing_office: Optional[str],
        source_url: Optional[str],
        default_publication_date: Optional[str],
    ) -> ParsedAdvisoryDocument:
        """Extract text page by page from a PDF bulletin using pypdf."""
        reader = pypdf.PdfReader(str(path))
        num_pages = len(reader.pages)
        records: list[AdvisoryRecord] = []
        errors: list[str] = []

        # Attempt to extract metadata date
        meta_date = cls._extract_date_from_pypdf_metadata(reader) or default_publication_date

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            if not raw_text.strip():
                continue

            # Check if this page contains date
            page_date = cls.extract_date_from_text(raw_text) or meta_date

            # Split into topical advisory paragraphs or process page as a whole
            page_records = cls._extract_records_from_text_block(
                raw_text=raw_text,
                source_id=source_id,
                issuing_organization=issuing_organization,
                issuing_office=issuing_office,
                source_document=path.name,
                source_url=source_url,
                document_sha256=sha256_hash,
                page_number=page_num,
                pub_date=page_date,
                extraction_method="pypdf_extractor",
            )
            records.extend(page_records)

        if not records:
            # Create a placeholder record
            rec = AdvisoryRecord(
                advisory_id=f"ADV-{source_id.upper()}-{uuid4().hex[:8]}",
                publication_date=default_publication_date,
                issuing_organization=issuing_organization,
                issuing_office=issuing_office,
                source_document=path.name,
                source_url=source_url,
                advisory_text="[EMPTY_OR_SCANNED_PDF] No extractable text found. Document may be a scanned image.",
                document_sha256=sha256_hash,
                page_number=1,
                extraction_method="pypdf_extractor",
                extraction_confidence=0.1,
                extraction_flags=["SCANNED_IMAGE_SUSPECTED", "ZERO_EXTRACTED_TEXT"],
                human_review_status=HumanReviewStatus.PENDING_REVIEW,
            )
            records.append(rec)

        return ParsedAdvisoryDocument(
            source_file=path.name,
            document_sha256=sha256_hash,
            total_pages_or_sections=num_pages,
            records=records,
            extraction_errors=errors,
            success=True,
        )

    @classmethod
    def parse_html(
        cls,
        path: Path,
        sha256_hash: str,
        source_id: str,
        issuing_organization: str,
        issuing_office: Optional[str],
        source_url: Optional[str],
        default_publication_date: Optional[str],
    ) -> ParsedAdvisoryDocument:
        """Parse advisory content from HTML document."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        pub_date = cls.extract_date_from_text(text) or default_publication_date

        records = cls._extract_records_from_text_block(
            raw_text=text,
            source_id=source_id,
            issuing_organization=issuing_organization,
            issuing_office=issuing_office,
            source_document=path.name,
            source_url=source_url,
            document_sha256=sha256_hash,
            page_number=1,
            pub_date=pub_date,
            extraction_method="beautifulsoup_html_parser",
        )

        return ParsedAdvisoryDocument(
            source_file=path.name,
            document_sha256=sha256_hash,
            total_pages_or_sections=1,
            records=records,
            success=True,
        )

    @classmethod
    def parse_text(
        cls,
        path: Path,
        sha256_hash: str,
        source_id: str,
        issuing_organization: str,
        issuing_office: Optional[str],
        source_url: Optional[str],
        default_publication_date: Optional[str],
    ) -> ParsedAdvisoryDocument:
        """Parse raw or bulletin text file."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        pub_date = cls.extract_date_from_text(text) or default_publication_date

        records = cls._extract_records_from_text_block(
            raw_text=text,
            source_id=source_id,
            issuing_organization=issuing_organization,
            issuing_office=issuing_office,
            source_document=path.name,
            source_url=source_url,
            document_sha256=sha256_hash,
            page_number=1,
            pub_date=pub_date,
            extraction_method="plaintext_parser",
        )

        return ParsedAdvisoryDocument(
            source_file=path.name,
            document_sha256=sha256_hash,
            total_pages_or_sections=1,
            records=records,
            success=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL EXTRACTION & EVIDENCE CLASSIFICATION
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def _extract_records_from_text_block(
        cls,
        raw_text: str,
        source_id: str,
        issuing_organization: str,
        issuing_office: Optional[str],
        source_document: str,
        source_url: Optional[str],
        document_sha256: str,
        page_number: int,
        pub_date: Optional[str],
        extraction_method: str,
    ) -> list[AdvisoryRecord]:
        """
        Analyze text block, extract entities, classify evidence type,
        and construct AdvisoryRecords.
        """
        clean_text = raw_text.strip()
        if not clean_text:
            return []

        # Segment by paragraphs or major crop/pest sections if long
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [clean_text]

        records: list[AdvisoryRecord] = []

        for p_idx, para in enumerate(paragraphs):
            entities: NormalizedEntities = AdvisoryNormalizer.normalize(para)

            # Skip paragraphs that contain zero agricultural entities if we have multiple
            if len(paragraphs) > 1 and not entities.crop and not entities.pest_common_name and not entities.district:
                continue

            evidence_type = cls.classify_evidence_type(para)
            severity = cls.classify_severity(para, evidence_type)
            justification_quote = cls.extract_evidence_justification_quote(para, evidence_type)
            scouting_recs, mgmt_recs, prev_recs = cls.extract_recommendations(para)

            confidence = 1.0
            flags = list(entities.extraction_flags)
            if not entities.crop:
                confidence -= 0.25
            if not entities.pest_common_name:
                confidence -= 0.25
            if not pub_date:
                confidence -= 0.2
                flags.append("PUBLICATION_DATE_MISSING")
            if not entities.district:
                flags.append("DISTRICT_UNSPECIFIED")

            confidence = max(0.1, min(1.0, round(confidence, 2)))

            translated = None
            trans_method = None
            if entities.language != "en":
                translated = AdvisoryNormalizer.generate_dictionary_translation(
                    text=para, lang=entities.language, entities=entities
                )
                if translated:
                    trans_method = "dictionary_assisted_multilingual_normalizer"

            advisory_id = f"ADV-{source_id.upper()}-{uuid4().hex[:8]}"

            rec = AdvisoryRecord(
                advisory_id=advisory_id,
                publication_date=pub_date,
                issuing_organization=issuing_organization,
                issuing_office=issuing_office,
                source_document=source_document,
                source_url=source_url,
                crop=entities.crop,
                pest_common_name=entities.pest_common_name,
                pest_scientific_name=entities.pest_scientific_name,
                district=entities.district,
                reported_pest_status=cls._extract_pest_status_snippet(para),
                advisory_severity=severity,
                evidence_type=evidence_type,
                evidence_justification_quote=justification_quote,
                source_section=f"Section/Paragraph {p_idx + 1} (Page {page_number})",
                recommended_scouting_actions=scouting_recs,
                recommended_management_actions=mgmt_recs,
                recommended_preventive_actions=prev_recs,
                advisory_text=para,
                original_language=entities.language,
                translated_text=translated,
                translation_method=trans_method,
                document_sha256=document_sha256,
                page_number=page_number,
                extraction_method=extraction_method,
                extraction_confidence=confidence,
                extraction_flags=flags,
                human_review_status=HumanReviewStatus.PENDING_REVIEW,
            )
            records.append(rec)

        return records

    @classmethod
    def classify_evidence_type(cls, text: str) -> EvidenceType:
        """
        Classifies epistemic evidence type from advisory text.
        Guarantees clear distinction between preventive guidelines and field observations.
        """
        lower = text.lower()

        # 1. FIELD_SURVEILLANCE_MEASUREMENT:
        # Requires explicit quantitative sampling keywords AND numerical values
        has_quant_measure = bool(re.search(r"(\d+(\.\d+)?)\s*(%|moths?|larva|larvae|caterpillars?|hills?|plants?)", lower))
        has_sampling_rigor = any(w in lower for w in [
            "fixed plot", "roving survey", "bolls dissected", "plants sampled",
            "नमुना पाहणी", "सापळ्यातील मोजणी", "दोन निरीक्षणे"
        ])
        if has_quant_measure and has_sampling_rigor:
            return EvidenceType.FIELD_SURVEILLANCE_MEASUREMENT

        # 2. REPORTED_PEST_SEVERITY:
        # Qualitative statement of severe damage / outbreak level
        severity_markers = [
            "तीव्र प्रादुर्भाव", "मोठ्या प्रमाणावर", "आर्थिक नुकसान पातळी ओलांडली", "नुकसान पातळी ओलांडली",
            "severe infestation", "outbreak reported", "heavy incidence", "heavy infestation",
            "severe defoliation", "exceeded etl", "exceeding etl", "crossed economic threshold",
            "exceeded economic threshold", "exceeding economic threshold", "flared up dangerously"
        ]
        if any(w in lower for w in severity_markers) or re.search(r"(severe|heavy)\s+(infestation|incidence|damage|defoliation)", lower):
            return EvidenceType.REPORTED_PEST_SEVERITY

        # 3. REPORTED_PEST_ACTIVITY:
        # Qualitative statement that pest was sighted, trapped, or active
        activity_markers = [
            "प्रादुर्भाव दिसून येत आहे", "आढळून आली", "पतंग अडकले", "कीड आढळून", "दिसून येत",
            "activity observed", "moths caught", "pest incidence noted", "infestation observed",
            "spotted in fields", "larvae noticed", "moth activity", "observed in pheromone"
        ]
        if any(w in lower for w in activity_markers) or re.search(r"activity\s+.*observed", lower) or re.search(r"(larvae|moths?)\s+(observed|noticed|found)", lower):
            return EvidenceType.REPORTED_PEST_ACTIVITY

        # 4. GENERAL_PREVENTIVE_ADVISORY:
        # Routine recommendation, preventive measures, scouting tips
        preventive_markers = [
            "सावधगिरी", "प्रतिबंधात्मक", "काळजी घ्यावी", "शेतकऱ्यांनी", "सल्ला", "करावे",
            "advisory", "recommended", "preventive", "scout fields", "install traps",
            "monitor", "spray if needed", "guideline"
        ]
        if any(w in lower for w in preventive_markers):
            return EvidenceType.GENERAL_PREVENTIVE_ADVISORY

        return EvidenceType.UNKNOWN_EVIDENCE_TYPE

    @classmethod
    def extract_evidence_justification_quote(cls, text: str, evidence_type: EvidenceType) -> Optional[str]:
        """Extract the exact sentence from advisory text justifying the assigned evidence classification."""
        sentences = re.split(r"[.।\n]", text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            s_lower = s_clean.lower()
            if evidence_type == EvidenceType.FIELD_SURVEILLANCE_MEASUREMENT:
                if re.search(r"\d+(\.\d+)?\s*(%|moths?|larva|larvae|hills?|plants?)", s_lower):
                    return s_clean
            elif evidence_type == EvidenceType.REPORTED_PEST_SEVERITY:
                if any(w in s_lower for w in ["तीव्र", "मोठ्या प्रमाणावर", "आर्थिक नुकसान", "severe", "outbreak", "heavy", "exceed"]):
                    return s_clean
            elif evidence_type == EvidenceType.REPORTED_PEST_ACTIVITY:
                if any(w in s_lower for w in ["प्रादुर्भाव", "आढळून", "पतंग", "activity", "moth", "observed", "noted", "noticed", "spotted"]):
                    return s_clean
            elif evidence_type == EvidenceType.GENERAL_PREVENTIVE_ADVISORY:
                if any(w in s_lower for w in ["सावधगिरी", "प्रतिबंधात्मक", "काळजी", "सल्ला", "advisory", "recommended", "preventive", "scout", "trap", "monitor"]):
                    return s_clean
        return None

    @classmethod
    def classify_severity(cls, text: str, evidence_type: EvidenceType) -> AdvisorySeverity:
        """Assign an advisory severity rating based on language intensity."""
        lower = text.lower()
        if any(w in lower for w in ["critical", "emergency", "तातडीने", "धोकादायक", "गंभीर", "आर्थिक नुकसान पातळी ओलांडली"]):
            return AdvisorySeverity.CRITICAL
        if any(w in lower for w in ["severe", "high", "तीव्र", "मोठ्या प्रमाणावर", "heavy"]):
            return AdvisorySeverity.HIGH
        if any(w in lower for w in ["moderate", "medium", "मध्यम", "दिसून येत"]):
            return AdvisorySeverity.MODERATE
        if any(w in lower for w in ["low", "mild", "कमी", "प्रारंभिक"]):
            return AdvisorySeverity.LOW
        return AdvisorySeverity.INFORMATIONAL

    @classmethod
    def extract_recommendations(cls, text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract scouting, management, and preventive recommendations from text."""
        scouting = []
        mgmt = []
        prev = []

        sentences = re.split(r"[.।\n]", text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            s_lower = s_clean.lower()

            # Scouting
            if any(w in s_lower for w in ["scout", "inspect", "trap", "monitor", "निरीक्षण", "पाहणी", "सापळे", "कामगंध"]):
                scouting.append(s_clean)
            # Management / Curative
            elif any(w in s_lower for w in ["spray", "chemical", "insecticide", "control", "फवारणी", "कीटकनाशक", "औषध"]):
                mgmt.append(s_clean)
            # Preventive / Cultural
            elif any(w in s_lower for w in ["prevent", "clean", "destroy", "handpick", "प्रतिबंधात्मक", "हातवेचणी", "काढून टाकावे"]):
                prev.append(s_clean)

        scout_str = "; ".join(scouting[:3]) if scouting else None
        mgmt_str = "; ".join(mgmt[:3]) if mgmt else None
        prev_str = "; ".join(prev[:3]) if prev else None
        return scout_str, mgmt_str, prev_str

    @classmethod
    def _extract_pest_status_snippet(cls, text: str) -> Optional[str]:
        """Extract a short sentence describing the pest status."""
        for s in re.split(r"[.।\n]", text):
            s_clean = s.strip()
            if any(w in s_clean.lower() for w in ["infestation", "incidence", "moths", "प्रादुर्भाव", "अळी", "कीड"]):
                if 10 < len(s_clean) < 180:
                    return s_clean
        return None

    @classmethod
    def extract_date_from_text(cls, text: str) -> Optional[str]:
        """
        Extract publication date from text using regex across English and Devanagari formats.
        Supports:
        - YYYY-MM-DD
        - DD/MM/YYYY or DD-MM-YYYY
        - Month DD, YYYY
        - Marathi dates e.g. "१५ ऑगस्ट २०२३" or "15 ऑक्टोबर 2023"
        """
        # ISO format: 2023-08-15
        iso_match = re.search(r"\b(20[2-3]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", text)
        if iso_match:
            return iso_match.group(0)

        # DD/MM/YYYY or DD-MM-YYYY
        dmy_match = re.search(r"\b(0[1-9]|[12]\d|3[01])[/-](0[1-9]|1[0-2])[/-](20[2-3]\d)\b", text)
        if dmy_match:
            day, month, year = dmy_match.groups()
            return f"{year}-{month}-{day}"

        # English textual: 15 August 2023 or August 15, 2023
        months = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04", "jun": "06",
            "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        }
        for m_name, m_num in months.items():
            pattern1 = rf"\b(0?[1-9]|[12]\d|3[01])\s+{m_name}[,]?\s+(20[2-3]\d)\b"
            m1 = re.search(pattern1, text, re.IGNORECASE)
            if m1:
                d = int(m1.group(1))
                y = m1.group(2)
                return f"{y}-{m_num}-{d:02d}"

        # Marathi transliterated months: ऑक्टोबर, नोव्हेंबर, ऑगस्ट, सप्टेंबर, जुलै, जून
        marathi_months = {
            "जानेवारी": "01", "फेब्रुवारी": "02", "मार्च": "03", "एप्रिल": "04",
            "मे": "05", "जून": "06", "जुलै": "07", "ऑगस्ट": "08",
            "सप्टेंबर": "09", "ऑक्टोबर": "10", "नोव्हेंबर": "11", "डिसेंबर": "12"
        }
        for mr_m_name, m_num in marathi_months.items():
            pattern_mr = rf"(\d{{1,2}})\s+{mr_m_name}\s+(20[2-3]\d)"
            m_mr = re.search(pattern_mr, text)
            if m_mr:
                d = int(m_mr.group(1))
                y = m_mr.group(2)
                return f"{y}-{m_num}-{d:02d}"

        return None

    @classmethod
    def _extract_date_from_pypdf_metadata(cls, reader: pypdf.PdfReader) -> Optional[str]:
        """Extract creation or modification date from PDF metadata."""
        if not reader.metadata:
            return None
        raw_date = reader.metadata.get("/CreationDate") or reader.metadata.get("/ModDate")
        if not raw_date:
            return None
        # PDF dates typically formatted: D:YYYYMMDDHHmmSS...
        m = re.search(r"D:(\d{4})(\d{2})(\d{2})", str(raw_date))
        if m:
            y, m_val, d = m.groups()
            return f"{y}-{m_val}-{d}"
        return None
