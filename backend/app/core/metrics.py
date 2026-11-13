"""Prometheus metrics definitions for AgriAdapt MLOps platform."""
from prometheus_client import Counter, Histogram, Gauge, Info

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
