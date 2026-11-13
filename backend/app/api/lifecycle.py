from __future__ import annotations

import datetime
import json
import uuid

from fastapi import APIRouter, status

from ..core.config import PROJECT_ROOT
from ..schemas.lifecycle import (
    LifecycleEvent,
    LifecycleLogRequest,
    LifecycleLogResponse,
)

router = APIRouter(prefix="/lifecycle", tags=["crop-lifecycle-mlops"])

LIFECYCLE_LOG_PATH = PROJECT_ROOT / "logs" / "crop_lifecycle_events.jsonl"
LIFECYCLE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

@router.post("/log", response_model=LifecycleLogResponse, status_code=status.HTTP_201_CREATED)
def record_lifecycle_event(payload: LifecycleLogRequest):
    event_id = str(uuid.uuid4())
    event_record = LifecycleEvent(
        id=event_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        zone_id=payload.zone_id,
        crop=payload.crop,
        stage=payload.stage,
        health_status=payload.health_status,
        metrics=payload.metrics,
        advisory_applied=payload.advisory_applied,
        harvest_yield_kg_per_acre=payload.harvest_yield_kg_per_acre,
        farmer_notes=payload.farmer_notes,
    )

    with LIFECYCLE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(event_record.model_dump_json() + "\n")

    history = get_all_events()
    return LifecycleLogResponse(
        status="recorded",
        event=event_record,
        lifecycle_history_count=len(history),
    )

@router.get("/history", response_model=list[LifecycleEvent])
def get_lifecycle_history(zone_id: str | None = None, crop: str | None = None):
    events = get_all_events()
    if zone_id:
        events = [e for e in events if e.zone_id.lower() == zone_id.lower()]
    if crop:
        events = [e for e in events if e.crop.lower() == crop.lower()]
    return events

def get_all_events() -> list[LifecycleEvent]:
    if not LIFECYCLE_LOG_PATH.exists():
        return []
    records: list[LifecycleEvent] = []
    with LIFECYCLE_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(LifecycleEvent(**data))
            except Exception:
                continue
    return records

