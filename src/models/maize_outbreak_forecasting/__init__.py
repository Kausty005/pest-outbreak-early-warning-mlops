"""
src/models/maize_outbreak_forecasting
─────────────────────────────────────
AgriAdapt AI: 7-Day Maize Disease Outbreak Forecasting Module.
Provides data audit, surveillance schemas, temporal label generators,
leakage-free temporal pipeline skeleton, and CNN diagnostic integration.
"""

from __future__ import annotations

from .schemas import (
    FieldSurveillanceObservation,
    DailyAgroclimaticRecord,
    ForecastingFeatureRecord,
    OutbreakPredictionTarget,
    MaizeDiseaseForecastRequest,
    MaizeDiseaseForecastResponse,
    MaizeGrowthStage,
    TargetDisease,
    DiseaseOccurrenceStatus,
)
from .labeling import (
    DiseaseOutbreakLabeler,
    OutbreakClassificationType,
)
from .feature_engineering import (
    TemporalFeatureEngineer,
    AgroclimaticDiseaseIndices,
)
from .pipeline import (
    MaizeDiseaseOutbreakPipeline,
    InsufficientSurveillanceDataError,
)
from .cnn_bridge import (
    CNNDiagnosticBridge,
)
from .data_audit import (
    audit_project_data_sufficiency,
    DataAuditResult,
)

__all__ = [
    "FieldSurveillanceObservation",
    "DailyAgroclimaticRecord",
    "ForecastingFeatureRecord",
    "OutbreakPredictionTarget",
    "MaizeDiseaseForecastRequest",
    "MaizeDiseaseForecastResponse",
    "MaizeGrowthStage",
    "TargetDisease",
    "DiseaseOccurrenceStatus",
    "DiseaseOutbreakLabeler",
    "OutbreakClassificationType",
    "TemporalFeatureEngineer",
    "AgroclimaticDiseaseIndices",
    "MaizeDiseaseOutbreakPipeline",
    "InsufficientSurveillanceDataError",
    "CNNDiagnosticBridge",
    "audit_project_data_sufficiency",
    "DataAuditResult",
]
