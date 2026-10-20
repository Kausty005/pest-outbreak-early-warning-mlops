from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "AgriAdapt Agricultural Intelligence API"
    api_prefix: str = "/api/v1"
    artifact_dir: Path = PROJECT_ROOT / "backend" / "artifacts"
    model_filename: str = "crop_model.joblib"
    metadata_filename: str = "metadata.json"
    fertilizer_model_filename: str = "fertilizer_model.joblib"
    fertilizer_metadata_filename: str = "fertilizer_model_metadata.json"
    fertilizer_schema_filename: str = "fertilizer_feature_schema.json"
    cors_origins: tuple[str, ...] = (
        "*",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    )
    persistence_enabled: bool = False
    database_url: str | None = None
    log_level: str = "INFO"

    @property
    def model_path(self) -> Path:
        return self.artifact_dir / self.model_filename

    @property
    def metadata_path(self) -> Path:
        return self.artifact_dir / self.metadata_filename

    @property
    def fertilizer_model_path(self) -> Path:
        primary = self.artifact_dir / self.fertilizer_model_filename
        if primary.exists():
            return primary
        default_dir = (PROJECT_ROOT / "backend" / "artifacts").resolve()
        if self.artifact_dir.resolve() == default_dir:
            fallback = PROJECT_ROOT / "models" / self.fertilizer_model_filename
            if fallback.exists():
                return fallback
        return primary

    @property
    def fertilizer_metadata_path(self) -> Path:
        primary = self.artifact_dir / self.fertilizer_metadata_filename
        if primary.exists():
            return primary
        default_dir = (PROJECT_ROOT / "backend" / "artifacts").resolve()
        if self.artifact_dir.resolve() == default_dir:
            fallback = PROJECT_ROOT / "models" / self.fertilizer_metadata_filename
            if fallback.exists():
                return fallback
        return primary

    @property
    def fertilizer_schema_path(self) -> Path:
        primary = self.artifact_dir / self.fertilizer_schema_filename
        if primary.exists():
            return primary
        return PROJECT_ROOT / "models" / self.fertilizer_schema_filename

    @classmethod
    def from_environment(cls) -> Settings:
        origins = tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "*,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
            ).split(",")
            if origin.strip()
        )
        artifact_dir = Path(os.getenv("MODEL_ARTIFACT_DIR", str(PROJECT_ROOT / "backend" / "artifacts")))
        return cls(
            artifact_dir=artifact_dir,
            cors_origins=origins or ("http://localhost:5173",),
            persistence_enabled=_as_bool(os.getenv("PERSISTENCE_ENABLED")),
            database_url=os.getenv("DATABASE_URL") or None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )


settings = Settings.from_environment()
