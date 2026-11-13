"""
surveillance_geospatial_alignment.py
────────────────────────────────────
Geospatial alignment module matching field surveillance observation coordinates
with environmental weather grid points and district centroids.

Implements:
- Haversine geodesic distance calculation
- Strict distance thresholds to prevent erroneous spatial linkage
- Explicit spatial uncertainty classification
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from src.data_ingestion.pest_surveillance.surveillance_schema import SurveillanceRecord

# Known district centroid coordinates from processed environmental dataset
KNOWN_DISTRICT_CENTROIDS: dict[str, tuple[float, float]] = {
    "nagpur": (21.124779, 79.115850),
    "amravati": (20.913883, 77.781160),
    "yavatmal": (20.421791, 78.138830),
    "jalgaon": (20.984182, 75.578094),
}

# Distance threshold limits (km)
MAX_PERMISSIBLE_MATCH_DISTANCE_KM = 60.0
HIGH_CONFIDENCE_GRID_DISTANCE_KM = 15.0
MODERATE_CONFIDENCE_DISTANCE_KM = 40.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance between two WGS84 points in kilometers.
    """
    r = 6371.0  # Earth mean radius in km

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(r * c, 2)


@dataclass
class GeospatialMatch:
    """Result of matching a surveillance observation with an environmental location."""
    observation_id: str
    surveillance_lat: float
    surveillance_lon: float
    matched_environmental_location: Optional[str]
    matched_lat: Optional[float]
    matched_lon: Optional[float]
    distance_km: Optional[float]
    spatial_confidence: str  # "HIGH_CONFIDENCE_GRID", "MODERATE_CENTROID_APPROX", "COARSE_REGIONAL", "SPATIAL_MISMATCH"
    is_matched: bool
    notes: str


def match_observation_to_environmental_grid(
    record: SurveillanceRecord,
    target_locations: Optional[dict[str, tuple[float, float]]] = None,
    max_distance_km: float = MAX_PERMISSIBLE_MATCH_DISTANCE_KM,
) -> GeospatialMatch:
    """
    Find the closest valid environmental grid or district centroid for an observation.

    Rejects spatial matches exceeding max_distance_km to prevent cross-district distortion.
    """
    locations = target_locations or KNOWN_DISTRICT_CENTROIDS

    best_loc: Optional[str] = None
    min_dist = float("inf")
    best_coords: Optional[tuple[float, float]] = None

    # First check if the declared district matches a known location
    norm_declared_dist = record.district.strip().lower()
    if norm_declared_dist in locations:
        target_lat, target_lon = locations[norm_declared_dist]
        dist = haversine_distance_km(record.latitude, record.longitude, target_lat, target_lon)
        if dist <= max_distance_km:
            min_dist = dist
            best_loc = norm_declared_dist
            best_coords = (target_lat, target_lon)

    # If declared district didn't match or exceeded tolerance, check nearest known location
    if best_loc is None:
        for loc_name, coords in locations.items():
            dist = haversine_distance_km(record.latitude, record.longitude, coords[0], coords[1])
            if dist < min_dist:
                min_dist = dist
                best_loc = loc_name
                best_coords = coords

    if min_dist > max_distance_km or best_loc is None or best_coords is None:
        return GeospatialMatch(
            observation_id=record.observation_id,
            surveillance_lat=record.latitude,
            surveillance_lon=record.longitude,
            matched_environmental_location=None,
            matched_lat=None,
            matched_lon=None,
            distance_km=round(min_dist, 2) if min_dist != float("inf") else None,
            spatial_confidence="SPATIAL_MISMATCH",
            is_matched=False,
            notes=(
                f"Nearest environmental station ({best_loc}) is {min_dist:.1f} km away, "
                f"exceeding maximum permissible spatial tolerance ({max_distance_km} km)."
            ),
        )

    # Determine confidence classification
    if min_dist <= HIGH_CONFIDENCE_GRID_DISTANCE_KM:
        confidence = "HIGH_CONFIDENCE_GRID"
        notes = f"Observation within {min_dist:.1f} km of localized environmental coordinates."
    elif min_dist <= MODERATE_CONFIDENCE_DISTANCE_KM:
        confidence = "MODERATE_CENTROID_APPROX"
        notes = (
            f"Observation matched to {best_loc.capitalize()} centroid at {min_dist:.1f} km. "
            "Microclimate represents district-scale atmospheric approximation."
        )
    else:
        confidence = "COARSE_REGIONAL"
        notes = (
            f"Observation matched to {best_loc.capitalize()} at {min_dist:.1f} km. "
            "High spatial uncertainty: local rainfall variability may diverge from centroid."
        )

    return GeospatialMatch(
        observation_id=record.observation_id,
        surveillance_lat=record.latitude,
        surveillance_lon=record.longitude,
        matched_environmental_location=best_loc.capitalize(),
        matched_lat=best_coords[0],
        matched_lon=best_coords[1],
        distance_km=min_dist,
        spatial_confidence=confidence,
        is_matched=True,
        notes=notes,
    )

