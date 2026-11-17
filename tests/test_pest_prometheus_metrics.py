"""
tests/test_pest_prometheus_metrics.py
─────────────────────────────────────
Verification tests for Prometheus pest forecasting metrics:
- pest_prediction_requests_total
- pest_prediction_latency_seconds
- pest_prediction_errors_total
- pest_model_info
- pest_model_drift
- FastAPI /metrics scrape endpoint
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_prometheus_metrics_endpoint_scrapes_successfully():
    """Verify backend /metrics endpoint returns HTTP 200 with Prometheus text format."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
    content = resp.text
    assert "# HELP" in content
    assert "# TYPE" in content


def test_pest_metrics_exposed_and_incremented_on_predict():
    """Verify that executing a prediction registers and updates pest-specific metrics."""
    # Execute a prediction
    payload = {
        "configuration": "ENVIRONMENTAL_ONLY",
        "crop": "Cotton",
        "pest": "Pink bollworm",
        "district": "Nagpur",
        "growth_stage": "Squaring",
        "t7_mean_temp_c": 31.5,
        "t7_min_temp_c": 26.0,
        "t7_max_temp_c": 36.5,
        "t7_mean_rh_pct": 78.0,
        "t7_rainfall_mm": 12.0,
        "t14_rainfall_mm": 40.0,
        "t7_mean_soil_moisture": 0.38,
        "t7_high_rh_days": 4,
        "t7_consecutive_dry_days": 2,
    }
    pred_resp = client.post("/api/v1/pest-forecasting/predict", json=payload)
    assert pred_resp.status_code == 200

    # Scrape /metrics
    metrics_resp = client.get("/metrics")
    metrics_text = metrics_resp.text

    # 1. pest_prediction_requests_total counter
    assert "pest_prediction_requests_total" in metrics_text
    assert 'configuration="environmental_only"' in metrics_text
    assert 'status="success"' in metrics_text

    # 2. pest_prediction_latency_seconds histogram
    assert "pest_prediction_latency_seconds_bucket" in metrics_text
    assert "pest_prediction_latency_seconds_count" in metrics_text

    # 3. pest_model_info gauge
    assert "pest_model_info" in metrics_text
    assert 'is_synthetic="true"' in metrics_text
    assert 'is_production_ready="false"' in metrics_text

    # 4. pest_model_drift gauge
    assert "pest_model_drift" in metrics_text
    assert 'metric="abs_diff"' in metrics_text
