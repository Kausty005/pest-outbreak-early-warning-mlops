"""Prometheus metrics definitions for AgriAdapt MLOps platform."""
from prometheus_client import Counter, Gauge, Histogram, Info

# Counters
prediction_requests_total = Counter(
    'agri_prediction_requests_total',
    'Total prediction requests',
    ['model', 'endpoint']
)
prediction_errors_total = Counter(
    'agri_prediction_errors_total',
    'Total prediction errors',
    ['model', 'endpoint']
)

# Histograms
prediction_latency_seconds = Histogram(
    'agri_prediction_latency_seconds',
    'Prediction latency',
    ['model'],
    buckets=[.01, .05, .1, .25, .5, 1.0, 2.5]
)
input_feature_value = Histogram(
    'agri_input_feature_value',
    'Input feature distribution',
    ['feature', 'model'],
    buckets=[0, 10, 25, 50, 75, 100, 150, 200, 300]
)

# Gauges
model_drift_score = Gauge(
    'agri_model_drift_score',
    'Current drift score',
    ['model']
)
active_zones = Gauge(
    'agri_active_farm_zones',
    'Number of active farm zones'
)
soil_moisture_gauge = Gauge(
    'agri_soil_moisture_pct',
    'Current soil moisture',
    ['zone']
)
soil_nitrogen_gauge = Gauge(
    'agri_soil_nitrogen_kgha',
    'Soil nitrogen',
    ['zone']
)

# Info
model_info_metric = Info(
    'agri_model',
    'Model metadata',
    ['model']
)

# ── Pest Forecasting MLOps Metrics (Version 2.0 Experimental) ─────────────
pest_prediction_requests_total = Counter(
    'pest_prediction_requests_total',
    'Total experimental pest forecasting prediction requests',
    ['configuration', 'status']
)

pest_prediction_errors_total = Counter(
    'pest_prediction_errors_total',
    'Total experimental pest forecasting prediction errors',
    ['error_type']
)

pest_prediction_latency_seconds = Histogram(
    'pest_prediction_latency_seconds',
    'Experimental pest forecasting inference latency in seconds',
    ['configuration'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

pest_model_info = Gauge(
    'pest_model_info',
    'Active experimental pest forecasting model metadata',
    ['model_version', 'configuration', 'framework', 'is_synthetic', 'is_production_ready']
)

pest_model_drift = Gauge(
    'pest_model_drift',
    'Experimental pest forecasting feature distribution drift indicator',
    ['feature', 'metric']
)

