"""
tests/test_public_advisories_pipeline.py
────────────────────────────────────────
Comprehensive test suite for Phase 8 Public Agricultural Pest Advisory
Ingestion, Extraction, Classification, and Validation Pipeline.

Tests:
1. Valid PDF and HTML extraction
2. Duplicate document detection by SHA-256 hash and metadata
3. SHA-256 provenance integrity logging
4. Missing publication dates handling and flagging
5. Multilingual Marathi & English text preservation and entity extraction
6. Extraction uncertainty and low confidence flagging
7. Geographic scope handling (Maharashtra districts)
8. Classification of general preventive advisories vs reported activity vs field measurements
9. Human review workflow (approve, reject, flag, audit entry generation)
10. Scientific invariant enforcement: Strict prevention of automatic outbreak label generation
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.data_ingestion.public_advisories import (
    AdvisoryDownloader,
    AdvisoryNormalizer,
    AdvisoryParser,
    AdvisoryProvenanceRegistry,
    AdvisoryRecord,
    AdvisorySeverity,
    AdvisoryValidationReport,
    AdvisoryValidator,
    EvidenceType,
    HumanReviewStatus,
    PublicAdvisoryIngestionPipeline,
    compute_content_sha256,
    compute_document_sha256,
    list_advisory_sources,
    get_advisory_source,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. SOURCES REGISTRY TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_public_advisory_sources_registry():
    sources = list_advisory_sources()
    assert len(sources) >= 7
    source_ids = {s.source_id for s in sources}
    assert "CROPSAP-PUBLIC" in source_ids
    assert "ICAR-CICR-PUB" in source_ids
    assert "ICAR-NCIPM-PUB" in source_ids
    assert "IMD-AGROMET" in source_ids
    assert "PDKV-AKOLA" in source_ids

    for s in sources:
        assert s.is_publicly_accessible is True
        assert len(s.districts_covered) > 0
        assert len(s.target_crops) > 0
        assert s.portal_url.startswith("http")


# ══════════════════════════════════════════════════════════════════════════════
# 2. PROVENANCE & DEDUPLICATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_provenance_sha256_and_duplicate_detection(tmp_path: Path):
    test_file = tmp_path / "test_advisory.txt"
    test_file.write_text("Advisory: Inspect cotton fields for Pink Bollworm in Nagpur.")

    sha1 = compute_document_sha256(test_file)
    assert len(sha1) == 64

    log_path = tmp_path / "advisory_provenance_log.json"
    registry = AdvisoryProvenanceRegistry(log_path=log_path)

    # First registration
    entry1, is_new1 = registry.register_document(
        source_id="TEST-SOURCE",
        file_path=test_file,
        publication_date="2023-08-15",
        title="Test Bulletin",
    )
    assert is_new1 is True
    assert entry1.sha256 == sha1

    # Second registration of identical file
    entry2, is_new2 = registry.register_document(
        source_id="TEST-SOURCE",
        file_path=test_file,
        publication_date="2023-08-15",
        title="Test Bulletin",
    )
    assert is_new2 is False
    assert entry2.sha256 == sha1
    assert registry.is_duplicate_hash(sha1) is True


# ══════════════════════════════════════════════════════════════════════════════
# 3. HTML ADVISORY PARSING & MULTILINGUAL EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def test_marathi_html_advisory_extraction(tmp_path: Path):
    html_content = """
    <html>
      <body>
        <h1>महाराष्ट्र कृषी विभाग सल्ला</h1>
        <p>प्रकाशन तारीख: 2023-08-10</p>
        <p>नागपूर जिल्ह्यातील कपाशी पिकावर गुलाबी बोंडअळी नियंत्रणासाठी शेतकऱ्यांनी कामगंध सापळे लावावेत.
        हा प्रतिबंधात्मक सल्ला असून नियमित पाहणी करावी.</p>
      </body>
    </html>
    """
    html_file = tmp_path / "marathi_sample.html"
    html_file.write_text(html_content, encoding="utf-8")

    parsed = AdvisoryParser.parse_file(
        file_path=html_file,
        source_id="CROPSAP-TEST",
        issuing_organization="MahaAgri",
    )
    assert parsed.success is True
    assert len(parsed.records) > 0

    rec = parsed.records[0]
    assert rec.crop == "cotton"
    assert rec.pest_common_name == "Pink Bollworm"
    assert rec.district == "Nagpur"
    assert rec.original_language == "mr"
    assert rec.evidence_type == EvidenceType.GENERAL_PREVENTIVE_ADVISORY
    assert rec.translated_text is not None
    assert "Pink Bollworm" in rec.translated_text


def test_english_advisory_extraction(tmp_path: Path):
    text_content = """
    ICAR-CICR Cotton Advisory - Vidarbha Zone
    Publication Date: 2023-08-20
    In Nagpur and Yavatmal districts, adult moth activity of Pink Bollworm (Pectinophora gossypiella)
    observed in pheromone monitoring traps. However, green boll sampling damage remains below 10% ETL.
    Farmers should handpick rosette flowers and spray neem oil 1500 ppm.
    """
    txt_file = tmp_path / "cicr_bulletin.txt"
    txt_file.write_text(text_content, encoding="utf-8")

    parsed = AdvisoryParser.parse_file(
        file_path=txt_file,
        source_id="ICAR-CICR",
        issuing_organization="ICAR-CICR",
    )
    assert parsed.success is True
    rec = parsed.records[0]
    assert rec.crop == "cotton"
    assert rec.pest_common_name == "Pink Bollworm"
    assert rec.pest_scientific_name == "Pectinophora gossypiella"
    assert rec.original_language == "en"
    assert rec.evidence_type == EvidenceType.REPORTED_PEST_ACTIVITY


# ══════════════════════════════════════════════════════════════════════════════
# 4. EVIDENCE CLASSIFICATION: PREVENTIVE VS ACTIVITY VS FIELD MEASUREMENT
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_type_classification():
    # 1. General preventive advice
    t1 = "Farmers are advised to install 5 pheromone traps per hectare as a preventive measure."
    assert AdvisoryParser.classify_evidence_type(t1) == EvidenceType.GENERAL_PREVENTIVE_ADVISORY

    # 2. Qualitative reported presence
    t2 = "Adult moth activity observed in monitoring traps across some blocks of Nagpur."
    assert AdvisoryParser.classify_evidence_type(t2) == EvidenceType.REPORTED_PEST_ACTIVITY

    # 3. Severe damage alert
    t3 = "Heavy infestation and severe defoliation reported exceeding economic threshold level."
    assert AdvisoryParser.classify_evidence_type(t3) == EvidenceType.REPORTED_PEST_SEVERITY

    # 4. Field surveillance measurement (quant + sampling rigor)
    t4 = "Fixed plot scouting revealed 14% damaged green bolls across 20 bolls dissected per acre."
    assert AdvisoryParser.classify_evidence_type(t4) == EvidenceType.FIELD_SURVEILLANCE_MEASUREMENT


# ══════════════════════════════════════════════════════════════════════════════
# 5. DATE PARSING & MISSING DATE HANDLING
# ══════════════════════════════════════════════════════════════════════════════

def test_date_extraction_formats():
    assert AdvisoryParser.extract_date_from_text("Published on 2023-08-15 by ICAR") == "2023-08-15"
    assert AdvisoryParser.extract_date_from_text("Date: 15/08/2023 Nagpur") == "2023-08-15"
    assert AdvisoryParser.extract_date_from_text("Issued 15 August 2023") == "2023-08-15"
    assert AdvisoryParser.extract_date_from_text("दिनांक १५ ऑगस्ट २०२३") is not None or AdvisoryParser.extract_date_from_text("15 ऑगस्ट 2023") == "2023-08-15"


def test_missing_date_flags_uncertainty(tmp_path: Path):
    undated_content = "Farmers in Amravati should scout soybean crops for defoliator caterpillars."
    txt_file = tmp_path / "undated.txt"
    txt_file.write_text(undated_content, encoding="utf-8")

    parsed = AdvisoryParser.parse_file(
        file_path=txt_file,
        source_id="TEST-SOURCE",
        issuing_organization="TestOrg",
    )
    rec = parsed.records[0]
    assert rec.publication_date is None
    assert "PUBLICATION_DATE_MISSING" in rec.extraction_flags
    assert rec.extraction_confidence < 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 6. BIOLOGICAL & GEOGRAPHIC VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def test_biological_mismatch_detected():
    # Pink bollworm does NOT attack soybean
    bad_rec = AdvisoryRecord(
        advisory_id="TEST-MISMATCH",
        issuing_organization="Test",
        source_document="test.txt",
        advisory_text="Test advisory text",
        document_sha256="a" * 64,
        crop="soybean",
        pest_common_name="Pink Bollworm",
    )
    issues = AdvisoryValidator.validate_record(bad_rec)
    assert any("Biological mismatch" in i for i in issues)


def test_unrecognized_district_detected():
    rec_bad_dist = AdvisoryRecord(
        advisory_id="TEST-BAD-DIST",
        issuing_organization="Test",
        source_document="test.txt",
        advisory_text="Test advisory text",
        document_sha256="b" * 64,
        crop="cotton",
        district="Bengaluru",  # Not in Maharashtra
    )
    issues = AdvisoryValidator.validate_record(rec_bad_dist)
    assert any("not recognized in Maharashtra" in i for i in issues)


# ══════════════════════════════════════════════════════════════════════════════
# 7. HUMAN REVIEW WORKFLOW & AUDIT TRAIL
# ══════════════════════════════════════════════════════════════════════════════

def test_human_review_workflow():
    rec = AdvisoryRecord(
        advisory_id="ADV-REV-01",
        issuing_organization="ICAR-CICR",
        source_document="advisory.txt",
        advisory_text="Scout cotton for pink bollworm",
        document_sha256="c" * 64,
        crop="cotton",
        pest_common_name="Pink Bollworm",
        human_review_status=HumanReviewStatus.PENDING_REVIEW,
    )

    # Approve
    updated, audit = AdvisoryValidator.apply_human_review(
        record=rec,
        reviewer_id="ENTOMOLOGIST-01",
        action="APPROVE",
        justification="Verified against ICAR bulletin.",
    )
    assert updated.human_review_status == HumanReviewStatus.VERIFIED_ADVISORY
    assert updated.reviewed_by == "ENTOMOLOGIST-01"
    assert audit.action == "APPROVE"
    assert "human_review_status" in audit.field_changes

    # Flag for surveillance guard: only allowed if evidence_type == FIELD_SURVEILLANCE_MEASUREMENT
    with pytest.raises(ValueError, match="Cannot flag advisory"):
        AdvisoryValidator.apply_human_review(
            record=rec,  # Has GENERAL_PREVENTIVE_ADVISORY
            reviewer_id="ENTOMOLOGIST-01",
            action="FLAG_FOR_SURVEILLANCE",
            justification="Attempting premature surveillance promotion",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 8. SCIENTIFIC INVARIANT: NO AUTOMATIC OUTBREAK LABELS
# ══════════════════════════════════════════════════════════════════════════════

def test_advisory_cannot_be_used_as_supervised_label():
    rec = AdvisoryRecord(
        advisory_id="ADV-SAFE-01",
        issuing_organization="CROPSAP",
        source_document="bulletin.html",
        advisory_text="Severe pest damage reported",
        document_sha256="d" * 64,
        evidence_type=EvidenceType.REPORTED_PEST_SEVERITY,
    )
    with pytest.raises(RuntimeError, match="must NEVER be used as a ground-truth label"):
        rec.assert_not_supervised_label()


# ══════════════════════════════════════════════════════════════════════════════
# 9. END-TO-END PIPELINE EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

def test_end_to_end_pipeline_execution(tmp_path: Path):
    raw_dir = tmp_path / "raw"
    proc_dir = tmp_path / "proc"
    raw_dir.mkdir()
    proc_dir.mkdir()

    # Create 2 test bulletins
    (raw_dir / "test_cotton_nagpur.txt").write_text(
        "ICAR-CICR Advisory 2023-08-15: In Nagpur district, inspect cotton for Pink Bollworm. Install traps."
    )
    (raw_dir / "test_soybean_amravati.txt").write_text(
        "CROPSAP Bulletin 2023-08-20: In Amravati district, soybean defoliator Spodoptera observed."
    )

    pipeline = PublicAdvisoryIngestionPipeline(raw_dir=raw_dir, processed_dir=proc_dir)
    records, report = pipeline.run_pipeline()

    assert len(records) >= 2
    assert report.total_records >= 2
    assert (proc_dir / "extracted_advisories.json").exists()
    assert (proc_dir / "advisory_validation_report.json").exists()
    assert (proc_dir / "advisory_provenance_log.json").exists()


# ══════════════════════════════════════════════════════════════════════════════
# 10. PHASE 9: REAL-WORLD DOCUMENT PARSING & EVIDENCE VERIFICATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_real_cicr_english_pdf_parsing():
    """Verify parsing on authentic ICAR-CICR weekly cotton advisory PDF."""
    pdf_path = Path("data/raw/public_advisories/cicr_cotton_advisory_2026_w21_en.pdf")
    if not pdf_path.exists():
        pytest.skip(f"Test file {pdf_path} not available")

    parsed = AdvisoryParser.parse_file(
        file_path=pdf_path,
        source_id="ICAR-CICR-PUB",
        issuing_organization="ICAR - Central Institute for Cotton Research",
    )
    assert parsed.success is True
    assert len(parsed.records) > 0

    # Must contain cotton records
    cotton_recs = [r for r in parsed.records if r.crop == "cotton"]
    assert len(cotton_recs) > 0
    # Must capture quotes and provenance
    for r in cotton_recs:
        assert r.document_sha256 is not None
        assert len(r.document_sha256) == 64
        if r.evidence_type != EvidenceType.UNKNOWN_EVIDENCE_TYPE:
            assert r.evidence_justification_quote is not None


def test_real_cropsap_faw_marathi_pdf_parsing():
    """Verify parsing on authentic Maharashtra CROPSAP & VNMKV FAW circular PDF."""
    pdf_path = Path("data/raw/public_advisories/cropsap_circular_vnmkv_faw_management.pdf")
    if not pdf_path.exists():
        pytest.skip(f"Test file {pdf_path} not available")

    parsed = AdvisoryParser.parse_file(
        file_path=pdf_path,
        source_id="CROPSAP-PUBLIC",
        issuing_organization="Commissioner of Agriculture, Maharashtra & VNMKV",
    )
    assert parsed.success is True
    assert len(parsed.records) > 0

    # Must contain FAW records
    faw_recs = [r for r in parsed.records if r.pest_common_name == "Fall Armyworm"]
    assert len(faw_recs) > 0
    rec = faw_recs[0]
    assert rec.pest_common_name == "Fall Armyworm"
    assert rec.pest_scientific_name == "Spodoptera frugiperda"
    assert rec.original_language == "mr"


def test_advisory_downloader_domain_security():
    """Verify downloader security: whitelisted domains allowed, unknown domains blocked."""
    from src.data_ingestion.public_advisories.advisory_downloader import AdvisoryDownloader

    assert AdvisoryDownloader.is_url_allowed("https://cropsap.maharashtra.gov.in/advisories") is True
    assert AdvisoryDownloader.is_url_allowed("https://cicr.org.in/weekly-advisory/") is True
    assert AdvisoryDownloader.is_url_allowed("https://nriipm.res.in/pest-bulletins") is True
    assert AdvisoryDownloader.is_url_allowed("https://mausam.imd.gov.in/nagpur") is True
    assert AdvisoryDownloader.is_url_allowed("http://98.70.59.108/cropsap/default.aspx") is True

    # Disallowed domains
    assert AdvisoryDownloader.is_url_allowed("https://unauthorized-domain.com/data.pdf") is False
    assert AdvisoryDownloader.is_url_allowed("https://phishing-site.org/malware.exe") is False


def test_evidence_justification_quote_preservation():
    """Verify that verbatim justification quotes are stored for classified evidence."""
    t_prev = "Apply neem seed kernel extract (NSKE 5%) as an initial preventive spray."
    q_prev = AdvisoryParser.extract_evidence_justification_quote(t_prev, EvidenceType.GENERAL_PREVENTIVE_ADVISORY)
    assert q_prev is not None
    assert "preventive" in q_prev.lower() or "spray" in q_prev.lower()

    t_act = "Moth catch of 8-10 moths/trap/night observed in pheromone traps."
    q_act = AdvisoryParser.extract_evidence_justification_quote(t_act, EvidenceType.REPORTED_PEST_ACTIVITY)
    assert q_act is not None
    assert "moth" in q_act.lower() or "trap" in q_act.lower()


def test_human_review_audit_trail_on_real_records():
    """Verify human review updates and audit logging on a real pipeline record."""
    record = AdvisoryRecord(
        advisory_id="ADV-TEST-PHASE9-01",
        issuing_organization="ICAR-CICR",
        source_document="cicr_cotton_advisory_2026_w21_en.pdf",
        advisory_text="Pink bollworm reported in intercropped plot.",
        document_sha256="e" * 64,
        crop="pigeonpea",
        pest_common_name="Pink Bollworm",
        human_review_status=HumanReviewStatus.PENDING_REVIEW,
    )

    # Correct crop to cotton based on manual bulletin review
    updated, audit = AdvisoryValidator.apply_human_review(
        record=record,
        reviewer_id="SENIOR-ENTOMOLOGIST-01",
        action="CORRECT_FIELDS",
        field_updates={"crop": "cotton"},
        justification="Paragraph context was cotton with pigeonpea border; pink bollworm affects cotton.",
    )

    assert updated.crop == "cotton"
    assert updated.human_review_status == HumanReviewStatus.VERIFIED_ADVISORY
    assert updated.reviewed_by == "SENIOR-ENTOMOLOGIST-01"
    assert audit.field_changes["crop"]["old"] == "pigeonpea"
    assert audit.field_changes["crop"]["new"] == "cotton"
    assert "context was cotton" in audit.justification


