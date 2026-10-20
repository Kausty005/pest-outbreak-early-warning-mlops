from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Farm(Base):
    __tablename__ = "farms"
    farm_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CropPrediction(Base):
    __tablename__ = "crop_predictions"
    prediction_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    farm_id: Mapped[str | None] = mapped_column(ForeignKey("farms.farm_id"), nullable=True, index=True)
    inputs: Mapped[dict] = mapped_column(JSON)
    predicted_crop: Mapped[str] = mapped_column(String(128))
    candidate_scores: Mapped[list] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PlantingRecord(Base):
    __tablename__ = "planting_records"
    planting_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.farm_id"), index=True)
    crop_id: Mapped[str] = mapped_column(String(128))
    planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(64), default="planned")


class FertilizerPrediction(Base):
    __tablename__ = "fertilizer_predictions"
    prediction_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    farm_id: Mapped[str | None] = mapped_column(ForeignKey("farms.farm_id"), nullable=True, index=True)
    crop: Mapped[str] = mapped_column(String(128))
    state_name: Mapped[str] = mapped_column(String(128))
    inputs: Mapped[dict] = mapped_column(JSON)
    recommendations: Mapped[dict] = mapped_column(JSON)
    commercial_equivalents: Mapped[dict] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    model_version: Mapped[str] = mapped_column(String(128), primary_key=True)
    training_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evaluation_metrics: Mapped[dict] = mapped_column(JSON)
    deployment_status: Mapped[str] = mapped_column(String(32), default="candidate")

