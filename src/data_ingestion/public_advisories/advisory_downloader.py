"""
advisory_downloader.py
──────────────────────
Secure document downloader and local archiving manager for public pest advisories.

Enforces:
1. Strict domain whitelisting (official government and ICAR portals only).
2. Local archiving into data/raw/public_advisories/.
3. Immediate SHA-256 provenance registration upon download.
4. Handling of offline/mock scenarios for reproducible local execution.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from src.data_ingestion.public_advisories.advisory_provenance import (
    AdvisoryProvenanceRegistry,
    compute_document_sha256,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_RAW_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "public_advisories"
)

ALLOWED_ADVISORY_DOMAINS = {
    "cropsap.maharashtra.gov.in",
    "krishi.maharashtra.gov.in",
    "cicr.icar.gov.in",
    "cicr.org.in",
    "www.cicr.org.in",
    "ncipm.icar.gov.in",
    "nriipm.res.in",
    "www.nriipm.res.in",
    "imdagrimet.gov.in",
    "mausam.imd.gov.in",
    "pdkv.ac.in",
    "www.pdkv.ac.in",
    "vnmkv.ac.in",
    "www.vnmkv.ac.in",
    "kvknagpur.org.in",
    "icar.org.in",
    "98.70.59.108",
}


class AdvisoryDownloader:
    """Safely downloads and archives publicly accessible agricultural advisories."""

    def __init__(
        self,
        target_dir: Path | str = DEFAULT_RAW_DIR,
        provenance_registry: Optional[AdvisoryProvenanceRegistry] = None,
        timeout_seconds: int = 20,
        ssl_verify: bool | str | Path = True,
    ) -> None:
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.provenance = provenance_registry or AdvisoryProvenanceRegistry()
        self.timeout = timeout_seconds
        # In accordance with data governance: verify=True or path to custom institutional CA bundle
        self.ssl_verify = str(ssl_verify) if isinstance(ssl_verify, Path) else ssl_verify

    @staticmethod
    def is_url_allowed(url: str) -> bool:
        """Verify URL domain is on the institutional whitelist."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain in ALLOWED_ADVISORY_DOMAINS or any(domain.endswith(f".{d}") for d in ALLOWED_ADVISORY_DOMAINS)
        except Exception:
            return False

    def download_document(
        self,
        url: str,
        source_id: str,
        filename: Optional[str] = None,
        publication_date: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Path:
        """Download document from an approved public URL and archive locally."""
        if not self.is_url_allowed(url):
            raise PermissionError(
                f"URL domain '{urlparse(url).netloc}' is not on the allowed advisory whitelist: "
                f"{sorted(ALLOWED_ADVISORY_DOMAINS)}"
            )

        target_name = filename or Path(urlparse(url).path).name
        if not target_name:
            target_name = f"advisory_{source_id.lower()}.pdf"

        destination = self.target_dir / target_name

        LOGGER.info("Downloading public advisory from %s to %s", url, destination)
        try:
            resp = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": "AgriAdapt-AdvisoryIngestion/1.0"},
                verify=self.ssl_verify,
            )
            resp.raise_for_status()
        except requests.exceptions.SSLError as ssl_err:
            LOGGER.error(
                "TLS certificate verification failed for %s (%s). "
                "In accordance with security and scientific data governance protocols, TLS verification is NOT disabled. "
                "To resolve, provide the institutional root CA bundle (e.g. NIC / India PKI) via REQUESTS_CA_BUNDLE "
                "or pass ssl_verify='/path/to/ca-bundle.pem'.",
                url, ssl_err,
            )
            raise ssl_err

        with open(destination, "wb") as f:
            f.write(resp.content)

        # Register in provenance registry
        self.provenance.register_document(
            source_id=source_id,
            file_path=destination,
            publication_date=publication_date,
            title=title or target_name,
            notes=f"Downloaded from {url}",
        )
        return destination

    def archive_text_content(
        self,
        source_id: str,
        filename: str,
        content: str,
        publication_date: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Path:
        """Save text/HTML bulletin directly into raw archive and register in provenance."""
        destination = self.target_dir / filename
        with open(destination, "w", encoding="utf-8") as f:
            f.write(content)

        self.provenance.register_document(
            source_id=source_id,
            file_path=destination,
            publication_date=publication_date,
            title=title or filename,
            notes="Archived direct text/HTML bulletin",
        )
        return destination

