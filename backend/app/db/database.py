from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import Settings
from .models import Base

LOGGER = logging.getLogger(__name__)


class DatabaseManager:
    """Optional persistence; a failed database never prevents model inference."""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.persistence_enabled
        self.available = False
        self._session_factory: sessionmaker | None = None
        if not self.enabled:
            LOGGER.info("Prediction persistence disabled by configuration")
            return
        if not settings.database_url:
            LOGGER.warning("PERSISTENCE_ENABLED=true but DATABASE_URL is absent; persistence disabled")
            self.enabled = False
            return
        try:
            engine = create_engine(settings.database_url, pool_pre_ping=True)
            Base.metadata.create_all(engine)
            self._session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            self.available = True
        except Exception:  # database is expressly non-critical for inference
            LOGGER.exception("Database initialization failed; continuing without prediction persistence")
            self.available = False

    def session(self) -> Session:
        if not self.available or self._session_factory is None:
            raise RuntimeError("Database persistence is unavailable")
        return self._session_factory()
