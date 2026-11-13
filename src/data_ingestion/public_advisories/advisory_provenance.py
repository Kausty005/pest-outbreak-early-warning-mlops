"""
advisory_provenance.py
──────────────────────
Cryptographic provenance, file integrity verification, and duplicate detection
for public agricultural advisory documents.

Tracks:
- Document SHA-256 hashes
- Ingestion timestamps and source attribution
- Duplicate detection by hash and by metadata (source, date, title)
- Audit log persistence at data/processed/public_advisories/advisory_provenance_log.json
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)

DEFAULT_PROVENANCE_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "public_advisories"
    / "advisory_provenance_log.json"
)


def compute_document_sha256(file_path: Path | str) -> str:
    """Compute the SHA-256 cryptographic hash of a document on disk."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Document file not found: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_content_sha256(content: bytes | str) -> str:
    """Compute the SHA-256 cryptographic hash of in-memory bytes or string."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


@dataclass
class DocumentProvenanceEntry:
    """Provenance record for a downloaded public advisory document."""
    document_id: str
    source_id: str
    filename: str
    file_path: str
    sha256: str
    file_size_bytes: int
    ingestion_timestamp: str
    publication_date: Optional[str] = None
    title: Optional[str] = None
    status: str = "INGESTED"  # "INGESTED", "PROCESSED", "EXTRACTION_FAILED", "DUPLICATE"
    extracted_records_count: int = 0
    notes: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdvisoryProvenanceRegistry:
    """
    Manages the provenance log of all ingested public advisory files.
    Enforces deduplication and SHA-256 integrity verification.
    """
    def __init__(self, log_path: Path | str = DEFAULT_PROVENANCE_PATH) -> None:
        self.log_path = Path(log_path)
        self.entries: dict[str, DocumentProvenanceEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load existing provenance log from disk if available."""
        if not self.log_path.exists():
            return
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                entry = DocumentProvenanceEntry(**item)
                self.entries[entry.sha256] = entry
            LOGGER.info("Loaded %d provenance records from %s", len(self.entries), self.log_path)
        except Exception as e:
            LOGGER.warning("Could not load provenance log from %s: %s", self.log_path, e)

    def save(self) -> None:
        """Persist provenance log to disk."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self.entries.values()], f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save provenance log to %s: %s", self.log_path, e)

    def is_duplicate_hash(self, sha256_hash: str) -> bool:
        """Check if a document with this identical SHA-256 hash has already been registered."""
        return sha256_hash in self.entries

    def find_duplicate_by_metadata(
        self,
        source_id: str,
        publication_date: Optional[str],
        title: Optional[str],
    ) -> Optional[DocumentProvenanceEntry]:
        """Check if a bulletin with the same source, date, and title exists."""
        if not publication_date or not title:
            return None
        norm_title = title.strip().lower()
        for entry in self.entries.values():
            if (
                entry.source_id.upper() == source_id.upper()
                and entry.publication_date == publication_date
                and entry.title
                and entry.title.strip().lower() == norm_title
            ):
                return entry
        return None

    def register_document(
        self,
        source_id: str,
        file_path: Path | str,
        publication_date: Optional[str] = None,
        title: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> tuple[DocumentProvenanceEntry, bool]:
        """
        Register a newly ingested advisory file.
        Returns (DocumentProvenanceEntry, is_new).
        """
        path = Path(file_path)
        sha256_hash = compute_document_sha256(path)

        if self.is_duplicate_hash(sha256_hash):
            existing = self.entries[sha256_hash]
            LOGGER.info("Document '%s' is an exact duplicate (SHA-256: %s)", path.name, sha256_hash[:12])
            return existing, False

        doc_id = f"DOC-{source_id.upper()}-{sha256_hash[:8]}"
        entry = DocumentProvenanceEntry(
            document_id=doc_id,
            source_id=source_id,
            filename=path.name,
            file_path=str(path.resolve()),
            sha256=sha256_hash,
            file_size_bytes=path.stat().st_size,
            ingestion_timestamp=datetime.utcnow().isoformat(),
            publication_date=publication_date,
            title=title,
            status="INGESTED",
            notes=notes,
        )
        self.entries[sha256_hash] = entry
        self.save()
        LOGGER.info("Registered document %s (%s)", doc_id, path.name)
        return entry, True

    def update_record_count(self, sha256_hash: str, count: int, status: str = "PROCESSED") -> None:
        """Update processed record count for a registered document."""
        if sha256_hash in self.entries:
            self.entries[sha256_hash].extracted_records_count = count
            self.entries[sha256_hash].status = status
            self.save()

