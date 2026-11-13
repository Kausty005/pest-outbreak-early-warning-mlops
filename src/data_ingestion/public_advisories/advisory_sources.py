"""
advisory_sources.py
───────────────────
Authoritative catalog of publicly accessible agricultural pest intelligence
and advisory sources for Maharashtra and India.

Records:
- Official organization name and institutional mandate
- Official website and specific portal URLs
- Publication formats (PDF, HTML, text bulletins)
- Geographic coverage (state, agro-climatic zones, districts)
- Crop and pest coverage
- Publication frequency and historical archive depth
- Access restrictions and terms of use
- Audit notes and verification dates
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class AdvisorySourceInfo:
    """Institutional metadata and accessibility profile for a public advisory source."""
    source_id: str
    organization_name: str
    issuing_office: str
    official_website: str
    portal_url: str
    available_formats: list[str]
    geographic_coverage: str
    districts_covered: list[str]
    target_crops: list[str]
    target_pests: list[str]
    publication_frequency: str
    historical_availability: str
    access_restriction: str  # "OPEN_PUBLIC", "PUBLIC_ARCHIVE", "REGISTRATION_REQUIRED"
    is_publicly_accessible: bool
    languages: list[str]  # e.g. ["en", "mr", "hi"]
    last_checked_date: str
    terms_of_use_summary: str
    audit_notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFIED PUBLIC ADVISORY SOURCES
# ══════════════════════════════════════════════════════════════════════════════

CROPSAP_PUBLIC_BULLETINS = AdvisorySourceInfo(
    source_id="CROPSAP-PUBLIC",
    organization_name="Department of Agriculture, Government of Maharashtra (MahaAgri)",
    issuing_office="Commissionerate of Agriculture, Extension & Training, Pune",
    official_website="https://krishi.maharashtra.gov.in/",
    portal_url="https://cropsap.maharashtra.gov.in/",
    available_formats=["PDF", "HTML"],
    geographic_coverage="Statewide Maharashtra (all 36 districts; Vidarbha, Marathwada, Khandesh)",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Wardha", "Nanded", "Jalna", "Buldhana", "Washim"],
    target_crops=["cotton", "soybean", "rice", "pigeonpea", "chickpea"],
    target_pests=[
        "Pink Bollworm (Pectinophora gossypiella)",
        "American Bollworm (Helicoverpa armigera)",
        "Tobacco Caterpillar (Spodoptera litura)",
        "Brown Planthopper (Nilaparvata lugens)",
        "Sucking pests (Aphids, Jassids, Thrips, Whiteflies)",
        "Soybean Girdle Beetle (Oberopsis brevis)",
    ],
    publication_frequency="Weekly / Bi-weekly during Kharif and Rabi seasons",
    historical_availability="Current season bulletins open; selective seasonal archive",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["mr", "en"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="Public government agricultural extension bulletins for farmer awareness and advisory use.",
    audit_notes=(
        "Public portal provides aggregate district advisory bulletins in Marathi and English. "
        "Unlike the internal micro-surveillance database, these bulletins are publicly downloadable "
        "and contain general pest emergence alerts and preventive recommendations."
    ),
)

MAHA_AGRI_PORTAL = AdvisorySourceInfo(
    source_id="MAHA-AGRI",
    organization_name="Department of Agriculture, Government of Maharashtra",
    issuing_office="Directorate of Agriculture, Extension & Training, Pune",
    official_website="https://krishi.maharashtra.gov.in/",
    portal_url="https://krishi.maharashtra.gov.in/en/crop-advisories/",
    available_formats=["PDF", "HTML"],
    geographic_coverage="Maharashtra state-level and division-level (Vidarbha, Nashik, Marathwada)",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Wardha", "Dhule"],
    target_crops=["cotton", "soybean", "rice", "maize", "pulses", "sugarcane"],
    target_pests=[
        "Pink Bollworm", "American Bollworm", "Spodoptera", "Fall Armyworm",
        "Stem Borer", "Leaf Folder", "Whitefly",
    ],
    publication_frequency="Fortnightly and seasonal milestone advisories",
    historical_availability="2022–Present seasonal releases",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["mr", "en"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="State government extension materials for farmer guidance and media publication.",
    audit_notes=(
        "Publishes seasonal pest management advisories ('Krishi Salla' / 'Pik Sanrakshan Salla'). "
        "Advisories provide IPM recommendations, threshold reminders, and weather-linked cautions."
    ),
)

ICAR_NCIPM_ADVISORIES = AdvisorySourceInfo(
    source_id="ICAR-NCIPM-PUB",
    organization_name="ICAR - National Research Institute for Integrated Pest Management (formerly NCIPM)",
    issuing_office="Crop Protection & Pest Surveillance Division, Pusa, New Delhi",
    official_website="https://nriipm.res.in/",
    portal_url="https://nriipm.res.in/",
    available_formats=["PDF", "HTML"],
    geographic_coverage="National coverage with dedicated Maharashtra cluster bulletins",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Wardha", "Akola"],
    target_crops=["cotton", "rice", "soybean", "maize", "mustard", "pulses"],
    target_pests=[
        "Pink Bollworm", "American Bollworm", "Fall Armyworm",
        "Brown Planthopper", "Tobacco Caterpillar", "Yellow Stem Borer",
    ],
    publication_frequency="Weekly / SMW-aligned during Kharif season",
    historical_availability="2020–Present annual archives",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["en", "hi"],
    last_checked_date="2024-11-13",
    terms_of_use_summary="Open access scientific research and public extension advisories under ICAR open access mandate.",
    audit_notes=(
        "Audited in Phase 9. Domain ncipm.icar.gov.in does not resolve; institution reorganized as "
        "ICAR-NRIIPM (National Research Institute for Integrated Pest Management) at nriipm.res.in. "
        "Publishes national and regional IPM guidance and advisory circulars."
    ),
)

ICAR_CICR_COTTON_ADVISORIES = AdvisorySourceInfo(
    source_id="ICAR-CICR-PUB",
    organization_name="ICAR - Central Institute for Cotton Research, Nagpur",
    issuing_office="Crop Protection Division / Extension Cell, Nagpur",
    official_website="https://cicr.org.in/",
    portal_url="https://cicr.org.in/weekly-advisory/",
    available_formats=["PDF", "HTML"],
    geographic_coverage="Central Cotton Zone (Vidarbha, Khandesh, Marathwada, Madhya Pradesh)",
    districts_covered=["Nagpur", "Wardha", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Buldhana"],
    target_crops=["cotton"],
    target_pests=[
        "Pink Bollworm (Pectinophora gossypiella)",
        "American Bollworm (Helicoverpa armigera)",
        "Spotted Bollworm (Earias spp.)",
        "Whitefly (Bemisia tabaci)",
        "Jassids (Amrasca biguttula biguttula)",
        "Thrips",
    ],
    publication_frequency="Weekly on Tuesdays during cotton growing season (June–December)",
    historical_availability="2018–Present archives available on official site",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["en", "hi", "mr"],
    last_checked_date="2024-11-13",
    terms_of_use_summary="ICAR open-access cotton crop management and pest management bulletins.",
    audit_notes=(
        "Audited in Phase 9. Domain cicr.icar.gov.in does not resolve; live portal is hosted at "
        "https://cicr.org.in/weekly-advisory/. Highest authority on cotton pest dynamics in Vidarbha Vertisols. "
        "Actively issues weekly bulletins in English, Marathi, and Hindi detailing trap catches and IPM actions."
    ),
)

PDKV_AKOLA_ADVISORIES = AdvisorySourceInfo(
    source_id="PDKV-AKOLA",
    organization_name="Dr. Panjabrao Deshmukh Krishi Vidyapeeth, Akola",
    issuing_office="Directorate of Extension Education / Regional Agromet Advisory Centre, Akola",
    official_website="https://www.pdkv.ac.in/",
    portal_url="https://www.pdkv.ac.in/agromet-advisories/",
    available_formats=["PDF"],
    geographic_coverage="Vidarbha agro-climatic region (Western and Eastern Vidarbha zones)",
    districts_covered=["Akola", "Amravati", "Yavatmal", "Nagpur", "Wardha", "Buldhana", "Washim"],
    target_crops=["cotton", "soybean", "pigeonpea", "chickpea", "sorghum"],
    target_pests=[
        "Pink Bollworm", "American Bollworm", "Tobacco Caterpillar",
        "Soybean Girdle Beetle", "Semilooper", "Pod Borer",
    ],
    publication_frequency="Bi-weekly (Tuesdays and Fridays)",
    historical_availability="Current season + 1 preceding year",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["mr", "en"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="University extension bulletin for Vidarbha farming community.",
    audit_notes=(
        "Provides localized agro-advisories combining IMD weather forecasts with regional pest scouting alerts. "
        "Published primarily in Marathi for local farmer comprehension."
    ),
)

VNMKV_PARBHANI_ADVISORIES = AdvisorySourceInfo(
    source_id="VNMKV-PARBHANI",
    organization_name="Vasantrao Naik Marathwada Krishi Vidyapeeth, Parbhani",
    issuing_office="Directorate of Extension Education, Parbhani",
    official_website="https://www.vnmkv.ac.in/",
    portal_url="https://www.vnmkv.ac.in/crop-advisory/",
    available_formats=["PDF"],
    geographic_coverage="Marathwada and adjacent Khandesh border districts",
    districts_covered=["Nanded", "Jalna", "Parbhani", "Beed", "Aurangabad", "Jalgaon"],
    target_crops=["cotton", "soybean", "pigeonpea", "sugarcane"],
    target_pests=["Pink Bollworm", "Tobacco Caterpillar", "Fall Armyworm", "Whitefly"],
    publication_frequency="Weekly",
    historical_availability="Current season bulletins",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["mr"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="University agricultural advisory and extension publications.",
    audit_notes=(
        "University extension bulletins addressing rainfed farming challenges in Marathwada and Khandesh. "
        "Contains actionable pesticide dosage sizing and bio-control guidelines."
    ),
)

IMD_AGROMET_PUNE = AdvisorySourceInfo(
    source_id="IMD-AGROMET",
    organization_name="India Meteorological Department (IMD) - Agrimet Division, Pune",
    issuing_office="Agromet Advisory Services Division, Shivajinagar, Pune 411005",
    official_website="https://imdagrimet.gov.in/",
    portal_url="https://imdagrimet.gov.in/district-advisories/",
    available_formats=["PDF", "HTML"],
    geographic_coverage="District-level coverage for all 36 Maharashtra districts",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Wardha", "Dhule"],
    target_crops=["cotton", "soybean", "rice", "maize", "pulses", "vegetables"],
    target_pests=[
        "Pink Bollworm", "American Bollworm", "Brown Planthopper",
        "Fall Armyworm", "Spodoptera", "Stem Borer",
    ],
    publication_frequency="Bi-weekly (Tuesdays and Fridays)",
    historical_availability="2019–Present comprehensive district archive",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["en", "mr"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="Government of India open data policy; public agromet bulletins.",
    audit_notes=(
        "District Agromet Advisory Service (DAAS) bulletins joint-issued with state agricultural universities. "
        "Correlates upcoming weather (rainfall, humidity, temperature) with impending pest and disease threats."
    ),
)

KVK_VIDARBHA_NETWORK = AdvisorySourceInfo(
    source_id="KVK-VIDARBHA",
    organization_name="Krishi Vigyan Kendra (KVK) Network - Vidarbha & Khandesh",
    issuing_office="KVK Nagpur, KVK Amravati (Durgapur), KVK Yavatmal, KVK Jalgaon (Pal)",
    official_website="https://icar.org.in/krishi-vigyan-kendras",
    portal_url="https://kvknagpur.org.in/advisories/",
    available_formats=["PDF", "HTML", "TXT"],
    geographic_coverage="District and taluka-specific agro-ecological clusters",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon"],
    target_crops=["cotton", "soybean", "rice", "maize", "chickpea"],
    target_pests=[
        "Pink Bollworm", "American Bollworm", "Tobacco Caterpillar",
        "Stem Borer", "Pod Borer", "Sucking pests",
    ],
    publication_frequency="Weekly and seasonal campaign releases",
    historical_availability="Recent 2 seasons",
    access_restriction="OPEN_PUBLIC",
    is_publicly_accessible=True,
    languages=["mr", "en"],
    last_checked_date="2024-11-12",
    terms_of_use_summary="ICAR extension system public awareness bulletins.",
    audit_notes=(
        "Field-level extension bulletins reflecting frontline demonstration plot experiences "
        "and farmer queries. Highly localized to Vidarbha talukas."
    ),
)


_ADVISORY_SOURCES: dict[str, AdvisorySourceInfo] = {
    CROPSAP_PUBLIC_BULLETINS.source_id: CROPSAP_PUBLIC_BULLETINS,
    MAHA_AGRI_PORTAL.source_id: MAHA_AGRI_PORTAL,
    ICAR_NCIPM_ADVISORIES.source_id: ICAR_NCIPM_ADVISORIES,
    ICAR_CICR_COTTON_ADVISORIES.source_id: ICAR_CICR_COTTON_ADVISORIES,
    PDKV_AKOLA_ADVISORIES.source_id: PDKV_AKOLA_ADVISORIES,
    VNMKV_PARBHANI_ADVISORIES.source_id: VNMKV_PARBHANI_ADVISORIES,
    IMD_AGROMET_PUNE.source_id: IMD_AGROMET_PUNE,
    KVK_VIDARBHA_NETWORK.source_id: KVK_VIDARBHA_NETWORK,
}


def list_advisory_sources() -> list[AdvisorySourceInfo]:
    """Return all investigated public pest advisory sources."""
    return list(_ADVISORY_SOURCES.values())


def get_advisory_source(source_id: str) -> Optional[AdvisorySourceInfo]:
    """Retrieve metadata for a specific advisory source."""
    return _ADVISORY_SOURCES.get(source_id.upper())

