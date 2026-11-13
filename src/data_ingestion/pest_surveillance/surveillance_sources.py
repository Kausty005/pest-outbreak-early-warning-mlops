"""
surveillance_sources.py
───────────────────────
Authoritative catalog of pest surveillance data sources for India and Maharashtra.

Documents:
- Organizations and institutional mandates
- Target crops and pest species
- Geographic coverage and observation frequencies
- Access methods, authentication requirements, and data-sharing agreements
- Downloadability audit results
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class SurveillanceSourceInfo:
    """Institutional metadata and accessibility profile for a pest surveillance source."""
    source_id: str
    organization: str
    program_name: str
    crops_covered: list[str]
    pest_species_covered: list[str]
    geographic_coverage: str
    districts_covered: list[str]
    observation_frequency: str
    historical_period: str
    data_format: str
    access_method: str
    is_publicly_downloadable: bool
    requires_institutional_agreement: bool
    responsible_authority: str
    official_portal_url: str
    contact_or_application_info: str
    data_sharing_requirements: list[str]
    audit_notes: str
    is_contact_verified: bool = False
    contact_verification_note: str = "Contact information not independently verified against official portal."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFIED SURVEILLANCE DATA SOURCES IN INDIA & MAHARASHTRA
# ══════════════════════════════════════════════════════════════════════════════

CROPSAP_MAHARASHTRA = SurveillanceSourceInfo(
    source_id="CROPSAP-MAHA",
    organization="Department of Agriculture, Government of Maharashtra (MahaAgri)",
    program_name="Crop Pest Surveillance and Advisory Project (CROPSAP)",
    crops_covered=["cotton", "soybean", "rice", "pigeonpea", "chickpea"],
    pest_species_covered=[
        "Pink Bollworm (Pectinophora gossypiella)",
        "American Bollworm (Helicoverpa armigera)",
        "Tobacco Caterpillar (Spodoptera litura)",
        "Brown Planthopper (Nilaparvata lugens)",
        "Sucking pests (Aphids, Jassids, Thrips, Whiteflies)",
        "Soybean Girdle Beetle (Oberopsis brevis)",
    ],
    geographic_coverage="Statewide Maharashtra (all 36 agricultural districts)",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Wardha", "Nanded", "Jalna"],
    observation_frequency="Semi-weekly (Fixed plots on Mondays, Roving survey plots on Thursdays)",
    historical_period="2009–Present (Active annually during Kharif and Rabi)",
    data_format="Relational Database (Oracle/MySQL) powering internal web & Android mobile client",
    access_method="Role-Based Access Control (RBAC) with employee credentials (Krishi Sahayak / TAO / DSAO)",
    is_publicly_downloadable=False,
    requires_institutional_agreement=True,
    responsible_authority="Director of Agriculture (Extension & Training) / State Nodal Officer CROPSAP, Pune",
    official_portal_url="https://cropsap.maharashtra.gov.in/",
    contact_or_application_info=(
        "Commissionerate of Agriculture, Government of Maharashtra, Central Building, "
        "Pune 411001. Email: cropsap.maha@gov.in / commagri.pune@gov.in"
    ),
    data_sharing_requirements=[
        "Formal written Memorandum of Understanding (MoU) with the Commissionerate of Agriculture, Pune.",
        "Non-Disclosure Agreement (NDA) restricting data use strictly to academic/non-commercial research.",
        "Institutional sponsorship letter from an accredited university or national research organization.",
        "Explicit geospatial anonymization to prevent farmer privacy disclosure.",
    ],
    audit_notes=(
        "CROPSAP is the gold-standard field surveillance system in Maharashtra. However, raw point-level "
        "and village-level time-series spreadsheets cannot be downloaded without formal ministerial authorization. "
        "Public web interface only displays aggregated district advisory bulletins in PDF format."
    ),
    is_contact_verified=False,
    contact_verification_note=(
        "Portal URL https://cropsap.maharashtra.gov.in/ confirmed publicly accessible (Nov 2024). "
        "Email addresses cropsap.maha@gov.in and commagri.pune@gov.in are listed in Maharashtra Agriculture "
        "Department communications but could not be independently confirmed via official portal contact page. "
        "Verify before sending formal correspondence."
    ),
)

ICAR_NCIPM = SurveillanceSourceInfo(
    source_id="ICAR-NCIPM",
    organization="ICAR - National Research Centre for Integrated Pest Management, New Delhi",
    program_name="National Pest Surveillance System & Cotton Pest Management System (CPMS)",
    crops_covered=["cotton", "rice", "soybean", "maize", "pulses", "mustard"],
    pest_species_covered=[
        "Pink Bollworm (Pectinophora gossypiella)",
        "American Bollworm (Helicoverpa armigera)",
        "Fall Armyworm (Spodoptera frugiperda)",
        "Brown Planthopper (Nilaparvata lugens)",
        "Yellow Stem Borer (Scirpophaga incertulas)",
        "Tobacco Caterpillar (Spodoptera litura)",
    ],
    geographic_coverage="National (Major agro-ecological zones across India, including Maharashtra clusters)",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Wardha", "Akola", "Bhatinda", "Coimbatore"],
    observation_frequency="Weekly scouting structured by Standard Meteorological Weeks (SMW 22–50)",
    historical_period="2000–Present",
    data_format="Structured database, ASP.NET monitoring application, and research publications",
    access_method="Institutional authentication for participating ICAR/SAU surveillance scientists",
    is_publicly_downloadable=False,
    requires_institutional_agreement=True,
    responsible_authority="Director, ICAR-NCIPM, LBS Building, Pusa Campus, New Delhi",
    official_portal_url="https://ncipm.icar.gov.in/",
    contact_or_application_info="Director, ICAR-NCIPM, Pusa Campus, New Delhi 110012. Email: director.ncipm@icar.gov.in",
    data_sharing_requirements=[
        "Formal inter-institutional research collaboration or ICAR Data Sharing Agreement.",
        "Compliance with ICAR Research Data Management Policy (2020).",
        "Clear specification of research objectives and intended machine learning applications.",
    ],
    audit_notes=(
        "Maintains national-level longitudinal pest surveillance records. Raw observation records are classified "
        "as restricted research data and require director-level approval."
    ),
    is_contact_verified=True,
    contact_verification_note=(
        "Portal URL https://ncipm.icar.gov.in/ confirmed accessible. Email director.ncipm@icar.gov.in "
        "is published on the official ICAR-NCIPM website contact page. Verified Nov 2024."
    ),
)

ICAR_CICR_NAGPUR = SurveillanceSourceInfo(
    source_id="ICAR-CICR",
    organization="ICAR - Central Institute for Cotton Research, Nagpur",
    program_name="Central India Cotton Pest Surveillance & Bt Resistance Monitoring",
    crops_covered=["cotton"],
    pest_species_covered=[
        "Pink Bollworm (Pectinophora gossypiella)",
        "American Bollworm (Helicoverpa armigera)",
        "Spotted Bollworm (Earias vitella)",
        "Whitefly (Bemisia tabaci)",
    ],
    geographic_coverage="Central Cotton Growing Zone (Vidarbha, Marathwada, Madhya Pradesh, Gujarat)",
    districts_covered=["Nagpur", "Wardha", "Amravati", "Yavatmal", "Jalgaon"],
    observation_frequency="Weekly pheromone trap catches (moths/trap/night) and destructive green boll dissection",
    historical_period="1995–Present",
    data_format="Research trial records, laboratory logs, scientific journals (Elsevier, Springer)",
    access_method="Direct academic research collaboration with Entomology Division, ICAR-CICR",
    is_publicly_downloadable=False,
    requires_institutional_agreement=True,
    responsible_authority="Director / Head of Crop Protection Division, ICAR-CICR Nagpur",
    official_portal_url="https://cicr.icar.gov.in/",
    contact_or_application_info=(
        "ICAR-Central Institute for Cotton Research, Post Bag No. 2, Shankarnagar P.O., "
        "Nagpur 440010, Maharashtra. Email: cicrnagpur@gmail.com"
    ),
    data_sharing_requirements=[
        "Approved collaborative research project (CRP) or academic thesis agreement.",
        "Co-authorship or explicit institutional attribution in derived publications.",
    ],
    audit_notes=(
        "Provides the most authoritative entomological validation for cotton bollworms in Vidarbha Vertisols. "
        "Aggregate results appear in published literature, but multi-year raw daily farm logs require direct MoU."
    ),
    is_contact_verified=False,
    contact_verification_note=(
        "Portal URL https://cicr.icar.gov.in/ is the official ICAR-CICR website. "
        "CAUTION: Email cicrnagpur@gmail.com is a Gmail address — verify the official institutional "
        "email from https://cicr.icar.gov.in/contact before sending formal correspondence. "
        "Official ICAR institute email typically follows the pattern director.cicr@icar.gov.in."
    ),
)

MAHARASHTRA_SAUS = SurveillanceSourceInfo(
    source_id="MAHA-SAUS",
    organization="State Agricultural Universities (Dr. PDKV Akola, VNMKV Parbhani, MPKV Rahuri)",
    program_name="All India Coordinated Research Projects (AICRP) & University Experimental Farms",
    crops_covered=["cotton", "soybean", "rice", "maize", "pulses"],
    pest_species_covered=[
        "Pink Bollworm", "American Bollworm", "Tobacco Caterpillar", "Fall Armyworm", "Brown Planthopper"
    ],
    geographic_coverage="Agro-climatic zones of Maharashtra",
    districts_covered=["Nagpur", "Amravati", "Yavatmal", "Jalgaon", "Akola", "Parbhani", "Rahuri"],
    observation_frequency="Weekly scouting during Kharif season",
    historical_period="2005–Present",
    data_format="Annual research reports, postgraduate dissertations, and departmental trial books",
    access_method="Formal request to Director of Research / Dean of Agriculture",
    is_publicly_downloadable=False,
    requires_institutional_agreement=True,
    responsible_authority="Director of Research, Dr. PDKV Akola / VNMKV Parbhani / MPKV Rahuri",
    official_portal_url="https://www.pdkv.ac.in/ / https://www.vnmkv.ac.in/",
    contact_or_application_info="Director of Research Office, Dr. PDKV, P.O. Krishi Nagar, Akola 444104, Maharashtra",
    data_sharing_requirements=[
        "Academic collaboration letter from department head.",
        "Agreement to cite university research stations and investigators.",
    ],
    audit_notes=(
        "Regional Agricultural Research Stations (RARS Amravati, ARS Yavatmal, ARS Jalgaon) hold localized "
        "high-quality plot surveillance, but datasets are archived in physical/tabular reports rather than open REST APIs."
    ),
    is_contact_verified=False,
    contact_verification_note=(
        "Dr. PDKV portal https://www.pdkv.ac.in/ is confirmed accessible. "
        "VNMKV portal https://www.vnmkv.ac.in/ is confirmed accessible. "
        "Physical address for Dr. PDKV Akola has been cross-referenced with university official publications. "
        "Contact the respective Director of Research office directly for data-access application procedures."
    ),
)


_ALL_SOURCES: dict[str, SurveillanceSourceInfo] = {
    CROPSAP_MAHARASHTRA.source_id: CROPSAP_MAHARASHTRA,
    ICAR_NCIPM.source_id: ICAR_NCIPM,
    ICAR_CICR_NAGPUR.source_id: ICAR_CICR_NAGPUR,
    MAHARASHTRA_SAUS.source_id: MAHARASHTRA_SAUS,
}


def list_authoritative_sources() -> list[SurveillanceSourceInfo]:
    """Return all investigated authoritative surveillance sources."""
    return list(_ALL_SOURCES.values())


def get_source_info(source_id: str) -> Optional[SurveillanceSourceInfo]:
    """Retrieve metadata for a specific surveillance source."""
    return _ALL_SOURCES.get(source_id.upper())


def generate_data_request_checklist() -> list[str]:
    """Checklist of requirements for formal institutional data-sharing applications."""
    return [
        "1. Institutional Affiliation Letter signed by Department Head or Dean.",
        "2. Formal Project Synopsis detailing the Early-Warning Machine Learning research objectives.",
        "3. Explicit list of requested fields (Observation Date, Taluka, Village, GPS Coordinates, Incidence %, Severity %, Trap Catches).",
        "4. Temporal and spatial boundaries requested (e.g., Kharif seasons 2021–2024 for Vidarbha & Khandesh).",
        "5. Signed Non-Disclosure Agreement (NDA) and farmer privacy anonymization undertaking.",
        "6. Data storage security compliance specification (local encrypted storage, no public redistribution of raw coordinates).",
    ]

