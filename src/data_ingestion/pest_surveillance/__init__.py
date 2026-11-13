"""
src/data_ingestion/pest_surveillance
────────────────────────────────────
Modular authentic pest surveillance data acquisition, validation,
geospatial matching, temporal alignment, and ground-truth labeling pipeline.

Enforces:
- Strict preservation of raw source files and missing values
- Authoritative provenance and cryptographic SHA-256 integrity verification
- IMD Standard Meteorological Week (SMW) and causal antecedent alignment
- Zero lookahead leakage in forward outbreak labeling [T+1, T+7]
- Active negative verification (no zero-fill inference)
"""
from src.data_ingestion.pest_surveillance.surveillance_geospatial_alignment import (
    HIGH_CONFIDENCE_GRID_DISTANCE_KM,
    KNOWN_DISTRICT_CENTROIDS,
    MAX_PERMISSIBLE_MATCH_DISTANCE_KM,
    GeospatialMatch,
    haversine_distance_km,
    match_observation_to_environmental_grid,
)
from src.data_ingestion.pest_surveillance.surveillance_labeling import (
    OFFICIAL_ETL_REGISTRY,
    VALID_ETL_VERIFICATION_STATUSES,
    EconomicThreshold,
    OutbreakLabelResult,
    compute_forward_outbreak_label,
    get_economic_threshold,
    resolve_stage_specific_density_threshold,
    resolve_stage_specific_threshold,
)
from src.data_ingestion.pest_surveillance.surveillance_loader import (
    LoadResult,
    compute_file_sha256,
    load_surveillance_file,
)
from src.data_ingestion.pest_surveillance.surveillance_schema import (
    MAHARASHTRA_BOUNDS,
    PHYSICAL_BOUNDS,
    VALID_CROP_PEST_COMBINATIONS,
    VALID_DATASET_CLASSIFICATIONS,
    SurveillanceRecord,
    normalize_token,
)
from src.data_ingestion.pest_surveillance.surveillance_sources import (
    CROPSAP_MAHARASHTRA,
    ICAR_CICR_NAGPUR,
    ICAR_NCIPM,
    MAHARASHTRA_SAUS,
    SurveillanceSourceInfo,
    generate_data_request_checklist,
    get_source_info,
    list_authoritative_sources,
)
from src.data_ingestion.pest_surveillance.surveillance_temporal_alignment import (
    TemporallyAlignedFeatures,
    calculate_smw,
    extract_antecedent_environmental_features,
)
from src.data_ingestion.pest_surveillance.surveillance_validation import (
    SurveillanceValidationReport,
    validate_surveillance_records,
)

__all__ = [
    # Schema
    "SurveillanceRecord",
    "MAHARASHTRA_BOUNDS",
    "PHYSICAL_BOUNDS",
    "VALID_CROP_PEST_COMBINATIONS",
    "VALID_DATASET_CLASSIFICATIONS",
    "normalize_token",
    # Sources
    "SurveillanceSourceInfo",
    "CROPSAP_MAHARASHTRA",
    "ICAR_NCIPM",
    "ICAR_CICR_NAGPUR",
    "MAHARASHTRA_SAUS",
    "list_authoritative_sources",
    "get_source_info",
    "generate_data_request_checklist",
    # Loader
    "LoadResult",
    "load_surveillance_file",
    "compute_file_sha256",
    # Validation
    "SurveillanceValidationReport",
    "validate_surveillance_records",
    # Geospatial
    "GeospatialMatch",
    "haversine_distance_km",
    "match_observation_to_environmental_grid",
    "KNOWN_DISTRICT_CENTROIDS",
    "MAX_PERMISSIBLE_MATCH_DISTANCE_KM",
    # Temporal
    "calculate_smw",
    "TemporallyAlignedFeatures",
    "extract_antecedent_environmental_features",
    # Labeling
    "EconomicThreshold",
    "OFFICIAL_ETL_REGISTRY",
    "VALID_ETL_VERIFICATION_STATUSES",
    "OutbreakLabelResult",
    "get_economic_threshold",
    "compute_forward_outbreak_label",
    "resolve_stage_specific_threshold",
    "resolve_stage_specific_density_threshold",
]

