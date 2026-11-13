"""
src/data_ingestion/public_advisories
────────────────────────────────────
Public Agricultural Pest Intelligence & Extension Advisory Ingestion Pipeline.

Collects, archives, extracts, normalizes, validates, and manages publicly
accessible agricultural advisories from government departments, ICAR research
institutes, state agricultural universities, and agrometeorological services.

CRITICAL SCIENTIFIC INVARIANT:
Public advisories represent institutional recommendations and regional intelligence.
They do NOT constitute verified field-level surveillance ground-truth observations
or outbreak labels. They must NEVER be used directly as supervised machine learning
training targets.
"""
from __future__ import annotations

from src.data_ingestion.public_advisories.advisory_schema import (
    AdvisoryRecord,
    AdvisorySeverity,
    EvidenceType,
    HumanReviewAuditEntry,
    HumanReviewStatus,
)
from src.data_ingestion.public_advisories.advisory_sources import (
    AdvisorySourceInfo,
    list_advisory_sources,
    get_advisory_source,
    CROPSAP_PUBLIC_BULLETINS,
    MAHA_AGRI_PORTAL,
    ICAR_NCIPM_ADVISORIES,
    ICAR_CICR_COTTON_ADVISORIES,
    PDKV_AKOLA_ADVISORIES,
    VNMKV_PARBHANI_ADVISORIES,
    IMD_AGROMET_PUNE,
    KVK_VIDARBHA_NETWORK,
)
from src.data_ingestion.public_advisories.advisory_provenance import (
    compute_document_sha256,
    compute_content_sha256,
    DocumentProvenanceEntry,
    AdvisoryProvenanceRegistry,
)
from src.data_ingestion.public_advisories.advisory_normalization import (
    AdvisoryNormalizer,
    NormalizedEntities,
    CROP_LEXICON,
    PEST_LEXICON,
    MAHARASHTRA_DISTRICTS,
)
from src.data_ingestion.public_advisories.advisory_parser import (
    AdvisoryParser,
    ParsedAdvisoryDocument,
)
from src.data_ingestion.public_advisories.advisory_validation import (
    AdvisoryValidator,
    AdvisoryValidationReport,
)
from src.data_ingestion.public_advisories.advisory_discovery import (
    AdvisoryDiscoveryService,
    DiscoveredAdvisoryItem,
)
from src.data_ingestion.public_advisories.advisory_downloader import (
    AdvisoryDownloader,
)
from src.data_ingestion.public_advisories.advisory_pipeline import (
    PublicAdvisoryIngestionPipeline,
)

__all__ = [
    # Schema
    "AdvisoryRecord",
    "AdvisorySeverity",
    "EvidenceType",
    "HumanReviewStatus",
    "HumanReviewAuditEntry",
    # Sources
    "AdvisorySourceInfo",
    "list_advisory_sources",
    "get_advisory_source",
    "CROPSAP_PUBLIC_BULLETINS",
    "MAHA_AGRI_PORTAL",
    "ICAR_NCIPM_ADVISORIES",
    "ICAR_CICR_COTTON_ADVISORIES",
    "PDKV_AKOLA_ADVISORIES",
    "VNMKV_PARBHANI_ADVISORIES",
    "IMD_AGROMET_PUNE",
    "KVK_VIDARBHA_NETWORK",
    # Provenance
    "compute_document_sha256",
    "compute_content_sha256",
    "DocumentProvenanceEntry",
    "AdvisoryProvenanceRegistry",
    # Normalization
    "AdvisoryNormalizer",
    "NormalizedEntities",
    "CROP_LEXICON",
    "PEST_LEXICON",
    "MAHARASHTRA_DISTRICTS",
    # Parser
    "AdvisoryParser",
    "ParsedAdvisoryDocument",
    # Validation
    "AdvisoryValidator",
    "AdvisoryValidationReport",
    # Discovery & Download
    "AdvisoryDiscoveryService",
    "DiscoveredAdvisoryItem",
    "AdvisoryDownloader",
    # Pipeline
    "PublicAdvisoryIngestionPipeline",
]
