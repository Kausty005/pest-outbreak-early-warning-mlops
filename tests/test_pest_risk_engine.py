"""
tests/test_pest_risk_engine.py
──────────────────────────────
Comprehensive unit and integration tests for the Explainable Environmental
Pest Risk Assessment Engine (Tier 1 Macro Early Warning).

Tests:
- Authoritative biological profile loading & validation
- Crop/pest rejection for unsupported combinations
- Biophysical response curves (thermal, hygrometric, precipitation, edaphic, phenology)
- Missing edaphic/phenological feature handling
- Partitioned antecedent vs forecast trend detection
- Mocked Open-Meteo live forecast acquisition and network failure tolerance
- Agronomic explainability and non-probabilistic disclaimers
"""
from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.pest_risk import (
    DISCLAIMER_TEXT,
    DailyWeatherRecord,
    PestBiologicalProfile,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    assess_pest_risk,
    categorize_favorability_risk,
    compute_daily_favorability,
    compute_humidity_favorability,
    compute_phenological_susceptibility,
    compute_precipitation_favorability,
    compute_soil_moisture_favorability,
    compute_temperature_favorability,
    fetch_open_meteo_forecast,
    get_pest_profile,
    get_supported_pest_profiles,
    list_supported_crops,
    list_supported_pests_for_crop,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. BIOLOGICAL PROFILES & SCIENTIFIC REGISTRY TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_registry_contains_five_authoritative_profiles():
    profiles = get_supported_pest_profiles()
    assert len(profiles) == 5

    expected_keys = [
        ("cotton", "pink_bollworm"),
        ("cotton", "american_bollworm"),
        ("soybean", "tobacco_caterpillar"),
        ("rice", "brown_planthopper"),
        ("maize", "fall_armyworm"),
    ]
    for key in expected_keys:
        assert key in profiles
        prof = profiles[key]
        assert isinstance(prof, PestBiologicalProfile)
        assert prof.thermal.t_base > 0.0
        assert prof.thermal.t_opt_min < prof.thermal.t_opt_max
        assert prof.thermal.t_opt_max < prof.thermal.t_upper
        assert prof.thermal.generation_degree_days > 200.0
        assert len(prof.sources) >= 2
        for src in prof.sources:
            assert src.url.startswith("http")
            assert src.year >= 1980


def test_supported_crops_and_pests_listing():
    crops = list_supported_crops()
    assert set(crops) == {"cotton", "soybean", "rice", "maize"}

    cotton_pests = list_supported_pests_for_crop("cotton")
    assert "pink_bollworm" in cotton_pests
    assert "american_bollworm" in cotton_pests


def test_get_pest_profile_default_pest():
    prof = get_pest_profile("cotton")
    assert prof.pest_id == "cotton_pink_bollworm"

    prof_soy = get_pest_profile("soybean")
    assert prof_soy.pest_id == "soybean_tobacco_caterpillar"


def test_get_pest_profile_unsupported_crop_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported crop 'sugarcane'"):
        get_pest_profile("sugarcane")


def test_get_pest_profile_unsupported_pest_for_crop_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported pest 'locust'"):
        get_pest_profile("cotton", "locust")


# ══════════════════════════════════════════════════════════════════════════════
# 2. BIOPHYSICAL SCORING CURVES TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_temperature_scoring_curves():
    prof = get_pest_profile("cotton", "pink_bollworm")
    thermal = prof.thermal  # t_base=12, opt=[25, 33], upper=38

    # Freezing or below base
    assert compute_temperature_favorability(10.0, thermal) == 0.0
    assert compute_temperature_favorability(12.0, thermal) == 0.0

    # Above upper lethal threshold
    assert compute_temperature_favorability(38.0, thermal) == 0.0
    assert compute_temperature_favorability(45.0, thermal) == 0.0

    # Optimal plateau
    assert compute_temperature_favorability(25.0, thermal) == 1.0
    assert compute_temperature_favorability(29.0, thermal) == 1.0
    assert compute_temperature_favorability(33.0, thermal) == 1.0

    # Monotonic ramp up
    score_18 = compute_temperature_favorability(18.5, thermal)
    score_22 = compute_temperature_favorability(22.0, thermal)
    assert 0.0 < score_18 < score_22 < 1.0

    # Monotonic decline past optimum
    score_35 = compute_temperature_favorability(35.5, thermal)
    assert 0.0 < score_35 < 1.0


def test_humidity_scoring_curves():
    prof = get_pest_profile("soybean", "tobacco_caterpillar")
    hygro = prof.hygrometric  # rh_crit=45, opt=[70, 90], pathogen=96

    # Extreme desiccation
    assert compute_humidity_favorability(20.0, hygro) < 0.05

    # Optimal plateau
    assert compute_humidity_favorability(75.0, hygro) == 1.0
    assert compute_humidity_favorability(88.0, hygro) == 1.0

    # Intermediate ramp
    score_55 = compute_humidity_favorability(55.0, hygro)
    assert 0.05 < score_55 < 1.0

    # Saturated relative humidity promotes natural fungal pathogens
    score_99 = compute_humidity_favorability(99.0, hygro)
    assert score_99 < 1.0
    assert score_99 >= 0.65


def test_precipitation_scoring_curves():
    prof = get_pest_profile("cotton", "pink_bollworm")
    precip = prof.precipitation  # fav=[2, 20], wash_off=40

    # Dry baseline
    dry_score = compute_precipitation_favorability(0.0, precip)
    assert dry_score == 0.70

    # Favorable showers
    fav_score = compute_precipitation_favorability(10.0, precip)
    assert fav_score == 1.0

    # Severe wash-off
    storm_score = compute_precipitation_favorability(65.0, precip)
    assert storm_score <= 0.30


def test_soil_moisture_scoring_curves():
    prof = get_pest_profile("cotton", "pink_bollworm")
    edaphic = prof.edaphic  # min=0.10, opt=[0.15, 0.35], max=0.45

    # Missing edaphic data handled cleanly
    assert compute_soil_moisture_favorability(None, edaphic) is None

    # Severely desiccated baked soil
    assert compute_soil_moisture_favorability(0.05, edaphic) < 0.15

    # Optimal pupation topsoil moisture
    assert compute_soil_moisture_favorability(0.25, edaphic) == 1.0

    # Waterlogged anaerobic soil
    assert compute_soil_moisture_favorability(0.50, edaphic) == 0.10


def test_phenology_scoring_curves():
    prof = get_pest_profile("cotton", "pink_bollworm")
    pheno = prof.phenology  # start=45, peak=[75, 125], end=160

    # When DSS is None, returns conservative default
    assert compute_phenological_susceptibility(None, pheno) == 0.85

    # Seedling stage (prior to squares/bolls)
    assert compute_phenological_susceptibility(20, pheno) == 0.10

    # Peak green boll stage
    assert compute_phenological_susceptibility(90, pheno) == 1.0

    # Senescent post-harvest
    assert compute_phenological_susceptibility(180, pheno) == 0.05


# ══════════════════════════════════════════════════════════════════════════════
# 3. DAILY COMPOSITE FAVORABILITY & RISK CATEGORIZATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_compute_daily_favorability_optimal_conditions():
    prof = get_pest_profile("cotton", "pink_bollworm")
    res = compute_daily_favorability(
        temp_c=28.0,
        rh_pct=75.0,
        rainfall_mm=5.0,
        soil_moisture_m3m3=0.25,
        days_since_sowing=90,
        pest_profile=prof,
    )
    assert res.temperature_score == 1.0
    assert res.humidity_score == 1.0
    assert res.rainfall_score == 1.0
    assert res.soil_moisture_score == 1.0
    assert res.phenology_score == 1.0
    assert res.composite_index == 1.0
    assert res.risk_category == "HIGH"
    assert res.edaphic_included is True


def test_compute_daily_favorability_temperature_gating():
    prof = get_pest_profile("cotton", "pink_bollworm")
    # Even if moisture and phenology are 100% optimal, freezing temperatures stop development
    res = compute_daily_favorability(
        temp_c=5.0,
        rh_pct=75.0,
        rainfall_mm=5.0,
        soil_moisture_m3m3=0.25,
        days_since_sowing=90,
        pest_profile=prof,
    )
    assert res.temperature_score == 0.0
    assert res.composite_index == 0.0
    assert res.risk_category == "LOW"


def test_compute_daily_favorability_missing_soil_moisture():
    prof = get_pest_profile("cotton", "pink_bollworm")
    res = compute_daily_favorability(
        temp_c=28.0,
        rh_pct=75.0,
        rainfall_mm=5.0,
        soil_moisture_m3m3=None,  # Missing edaphic data
        days_since_sowing=90,
        pest_profile=prof,
    )
    assert res.soil_moisture_score is None
    assert res.edaphic_included is False
    assert res.composite_index == 1.0
    assert res.risk_category == "HIGH"


def test_categorize_favorability_risk():
    assert categorize_favorability_risk(0.20) == "LOW"
    assert categorize_favorability_risk(0.39) == "LOW"
    assert categorize_favorability_risk(0.40) == "MODERATE"
    assert categorize_favorability_risk(0.69) == "MODERATE"
    assert categorize_favorability_risk(0.70) == "HIGH"
    assert categorize_favorability_risk(0.95) == "HIGH"


# ══════════════════════════════════════════════════════════════════════════════
# 4. TREND ANALYSIS & ORCHESTRATION INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_assess_pest_risk_detects_rising_trend():
    # Antecedent: dry/cool (low favorability)
    antecedent = [
        DailyWeatherRecord(date="2023-08-01", temp_mean=18.0, humidity_mean=40.0, rainfall_mm=0.0),
        DailyWeatherRecord(date="2023-08-02", temp_mean=18.5, humidity_mean=42.0, rainfall_mm=0.0),
    ]
    # Forecast: warm/humid (high favorability)
    forecast = [
        DailyWeatherRecord(date="2023-08-03", temp_mean=28.0, humidity_mean=80.0, rainfall_mm=8.0),
        DailyWeatherRecord(date="2023-08-04", temp_mean=29.0, humidity_mean=82.0, rainfall_mm=10.0),
    ]

    req = RiskAssessmentRequest(
        crop="cotton",
        pest="pink_bollworm",
        location_name="Nagpur",
        latitude=21.1458,
        longitude=79.0882,
        planting_date="2023-06-01",
        antecedent_weather=antecedent,
        forecast_weather=forecast,
    )

    resp = assess_pest_risk(req)
    assert resp.risk_trend == "RISING"
    assert resp.forecast_mean_favorability > resp.antecedent_mean_favorability + 0.10
    assert any("TREND WARNING (RISING RISK)" in r for r in resp.recommendations)


def test_assess_pest_risk_detects_declining_trend():
    # Antecedent: warm/humid (high favorability)
    antecedent = [
        DailyWeatherRecord(date="2023-08-01", temp_mean=28.0, humidity_mean=80.0, rainfall_mm=8.0),
        DailyWeatherRecord(date="2023-08-02", temp_mean=29.0, humidity_mean=82.0, rainfall_mm=10.0),
    ]
    # Forecast: torrential storm (dislodgement) or severe dry heat
    forecast = [
        DailyWeatherRecord(date="2023-08-03", temp_mean=42.0, humidity_mean=20.0, rainfall_mm=0.0),
        DailyWeatherRecord(date="2023-08-04", temp_mean=43.0, humidity_mean=18.0, rainfall_mm=0.0),
    ]

    req = RiskAssessmentRequest(
        crop="cotton",
        pest="pink_bollworm",
        location_name="Nagpur",
        latitude=21.1458,
        longitude=79.0882,
        planting_date="2023-06-01",
        antecedent_weather=antecedent,
        forecast_weather=forecast,
    )

    resp = assess_pest_risk(req)
    assert resp.risk_trend == "DECLINING"
    assert resp.forecast_mean_favorability < resp.antecedent_mean_favorability - 0.10
    assert any("DECLINING RISK" in r for r in resp.recommendations)


# ══════════════════════════════════════════════════════════════════════════════
# 5. MOCKED LIVE FORECAST ACQUISITION & FAULT TOLERANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════

@patch("urllib.request.urlopen")
def test_fetch_open_meteo_forecast_success(mock_urlopen):
    mock_payload = {
        "daily": {
            "time": ["2023-08-10", "2023-08-11"],
            "temperature_2m_mean": [28.2, 27.9],
            "temperature_2m_max": [33.0, 32.5],
            "temperature_2m_min": [24.0, 23.5],
            "relative_humidity_2m_mean": [76.0, 80.0],
            "precipitation_sum": [4.5, 12.0],
            "soil_moisture_0_to_7cm_mean": [0.28, 0.31],
        }
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    records, err = fetch_open_meteo_forecast(21.14, 79.08, days=2)
    assert err is None
    assert len(records) == 2
    assert records[0].date == "2023-08-10"
    assert records[0].temp_mean == 28.2
    assert records[0].soil_moisture_m3m3 == 0.28


@patch("urllib.request.urlopen")
def test_assess_pest_risk_handles_network_failure_gracefully(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("DNS resolution failed")

    antecedent = [
        DailyWeatherRecord(date="2023-08-01", temp_mean=28.0, humidity_mean=75.0, rainfall_mm=5.0),
    ]

    req = RiskAssessmentRequest(
        crop="soybean",
        pest="tobacco_caterpillar",
        location_name="Amravati",
        latitude=20.93,
        longitude=77.75,
        planting_date="2023-06-20",
        antecedent_weather=antecedent,
        fetch_live_forecast=True,
    )

    # Engine must not crash on network error
    resp = assess_pest_risk(req)
    assert resp.risk_trend == "UNKNOWN"
    assert resp.forecast_mean_favorability is None
    assert len(resp.forecast_days) == 0
    assert any("Live forecast unavailable" in notice for notice in resp.data_notices)


# ══════════════════════════════════════════════════════════════════════════════
# 6. EXPLAINABILITY, CITATIONS & NON-PROBABILISTIC DISCLAIMER TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_explainability_payload_and_disclaimer():
    antecedent = [
        DailyWeatherRecord(
            date="2023-08-15",
            temp_mean=27.5,
            humidity_mean=78.0,
            rainfall_mm=8.0,
            soil_moisture_m3m3=0.30,
        ),
    ]
    req = RiskAssessmentRequest(
        crop="cotton",
        pest="pink_bollworm",
        location_name="Yavatmal",
        latitude=20.39,
        longitude=78.12,
        planting_date="2023-06-15",
        antecedent_weather=antecedent,
    )
    resp = assess_pest_risk(req)

    # Check disclaimer
    assert DISCLAIMER_TEXT in resp.disclaimer
    assert "NOT a calibrated statistical outbreak probability" in resp.disclaimer

    # Check drivers
    assert len(resp.favorable_drivers) > 0
    assert any("Ambient temperature" in d for d in resp.favorable_drivers)

    # Check IPM recommendations
    assert len(resp.recommendations) >= 2

    # Check scientific citations
    assert len(resp.scientific_citations) >= 2
    for cite in resp.scientific_citations:
        assert "title" in cite
        assert "authors" in cite
        assert "year" in cite
        assert "url" in cite
        assert "key_finding" in cite
