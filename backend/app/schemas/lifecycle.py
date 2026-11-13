from __future__ import annotations

import datetime
from typing import Literal
from pydantic import BaseModel, Field

class LifecycleEvent(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    zone_id: str
    crop: str
    stage: Literal["SEEDLING", "VEGETATIVE", "FLOWERING", "FRUITING_GRAIN_FILL", "MATURITY", "HARVEST_COMPLETED"]
    health_status: Literal["HEALTHY", "STRESSED", "DISEASE_PRONE", "DEFICIENT", "CRITICAL"]
    metrics: dict[str, float] = Field(default_factory=dict, description="N, P, K, moisture, temp, etc.")
    advisory_applied: list[str] = Field(default_factory=list)
    harvest_yield_kg_per_acre: float | None = None
    farmer_notes: str | None = None

class LifecycleLogRequest(BaseModel):
    zone_id: str
    crop: str
    stage: Literal["SEEDLING", "VEGETATIVE", "FLOWERING", "FRUITING_GRAIN_FILL", "MATURITY", "HARVEST_COMPLETED"]
    health_status: Literal["HEALTHY", "STRESSED", "DISEASE_PRONE", "DEFICIENT", "CRITICAL"]
    metrics: dict[str, float] = Field(default_factory=dict)
    advisory_applied: list[str] = Field(default_factory=list)
    harvest_yield_kg_per_acre: float | None = None
    farmer_notes: str | None = None

class LifecycleLogResponse(BaseModel):
    status: str = "recorded"
    event: LifecycleEvent
    lifecycle_history_count: int

