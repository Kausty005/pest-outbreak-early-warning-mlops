"""
backend/app/core/crop_catalog.py
─────────────────────────────────
Centralized Crop Catalog & Single Source of Truth for AgriAdapt AI MLOps Platform.
Loads, indexes, and queries the master configuration in `config/crops.json`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "config" / "crops.json"


class CropNotFoundError(KeyError):
    """Raised when an unknown crop identifier or alias is queried."""


class CropCatalog:
    """
    In-memory indexed interface over `config/crops.json`.
    Provides fast O(1) canonical resolution and model-specific mapping.
    """

    def __init__(self, catalog_path: Path | str = DEFAULT_CATALOG_PATH) -> None:
        self.catalog_path = Path(catalog_path)
        self._data: dict[str, Any] = {}
        self._by_canonical: dict[str, dict[str, Any]] = {}
        self._alias_map: dict[str, str] = {}
        self.reload()

    def reload(self) -> None:
        """Reload and rebuild indices from the JSON configuration."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Crop configuration not found at {self.catalog_path}")

        with open(self.catalog_path, encoding="utf-8") as f:
            self._data = json.load(f)

        self._by_canonical.clear()
        self._alias_map.clear()

        for crop in self._data.get("crops", []):
            cid = crop["canonical_id"].lower()
            self._by_canonical[cid] = crop

            # Index canonical ID
            self._alias_map[cid] = cid

            # Index display name
            disp = crop.get("display_name", "").lower()
            if disp:
                self._alias_map[disp] = cid

            # Index accepted aliases
            for alias in crop.get("accepted_aliases", []):
                self._alias_map[alias.lower().strip()] = cid

            # Index model identifiers
            models = crop.get("models", {})
            crop_pred = models.get("crop_prediction", {})
            if crop_pred.get("model_identifier"):
                self._alias_map[crop_pred["model_identifier"].lower().strip()] = cid

            fert = models.get("fertilizer_recommendation", {})
            for f_id in fert.get("model_identifiers", []):
                self._alias_map[f_id.lower().strip()] = cid

    @property
    def metadata(self) -> dict[str, Any]:
        return self._data.get("metadata", {})

    def resolve_canonical_id(self, name: str) -> str | None:
        """Resolve any crop name, alias, or model identifier to its canonical ID."""
        if not name:
            return None
        cleaned = name.strip().lower()
        if cleaned in self._alias_map:
            return self._alias_map[cleaned]

        # Partial matching fallback heuristics
        if "cotton" in cleaned or "kapas" in cleaned:
            return "cotton"
        if "rice" in cleaned or "paddy" in cleaned or "dhan" in cleaned:
            return "rice"
        if "maize" in cleaned or "corn" in cleaned or "makka" in cleaned:
            return "maize"
        if "wheat" in cleaned or "gehun" in cleaned:
            return "wheat"
        if "sugarcane" in cleaned or "ganna" in cleaned:
            return "sugarcane"
        if "chickpea" in cleaned or "chana" in cleaned or "gram" in cleaned:
            return "chickpea"
        if "pigeonpea" in cleaned or "tur" in cleaned or "arhar" in cleaned:
            return "pigeonpeas"

        return None

    def get_crop(self, name: str) -> dict[str, Any] | None:
        """Get the full crop specification by canonical ID or any accepted alias."""
        cid = self.resolve_canonical_id(name)
        if cid:
            return self._by_canonical.get(cid)
        return None

    def get_display_name(self, name: str) -> str:
        """Get formatted display name for a crop."""
        crop = self.get_crop(name)
        return crop["display_name"] if crop else name

    def get_crop_prediction_label(self, name: str) -> str | None:
        """Get the exact label used by the crop recommendation model (e.g. 'rice', 'cotton')."""
        crop = self.get_crop(name)
        if not crop:
            return None
        pred = crop.get("models", {}).get("crop_prediction", {})
        if pred.get("supported"):
            return pred.get("model_identifier")
        return None

    def get_fertilizer_identifier(self, name: str, season: str | None = None) -> str:
        """
        Get the exact crop identifier required by the ICAR-IISS fertilizer model.
        Resolves seasonal identifiers (e.g. 'Kharif Maize', 'Rabi Maize', 'Rice')
        or falls back to the configured default baseline ('Rice').
        """
        crop = self.get_crop(name)
        if not crop:
            return "Rice"

        fert = crop.get("models", {}).get("fertilizer_recommendation", {})
        if not fert.get("supported"):
            return fert.get("default_identifier", "Rice")

        supported_ids = fert.get("model_identifiers", [])
        if not supported_ids:
            return fert.get("default_identifier", "Rice")

        if len(supported_ids) == 1:
            return supported_ids[0]

        # Handle seasonal distinctions if multiple identifiers exist
        if season:
            s_clean = season.strip().lower()
            for fid in supported_ids:
                if s_clean in fid.lower():
                    return fid

        return fert.get("default_identifier", supported_ids[0])

    def list_all_crops(self) -> list[dict[str, Any]]:
        """Return all catalog crop objects."""
        return list(self._by_canonical.values())

    def list_supported_crops(self, model: str) -> list[dict[str, Any]]:
        """
        Filter crops by supported model:
        'crop_prediction', 'fertilizer_recommendation', 'pest_outbreak_preview', 'pest_outbreak_prediction'
        """
        results = []
        for crop in self._by_canonical.values():
            if model == "pest_outbreak_prediction":
                if crop.get("pest_outbreak_prediction", {}).get("eligible", False):
                    results.append(crop)
            else:
                m = crop.get("models", {}).get(model, {})
                if m.get("supported", False):
                    results.append(crop)
        return results

    def list_pest_eligible_crops(self, priority: str | None = None) -> list[dict[str, Any]]:
        """List crops eligible for the future pest outbreak detection model."""
        eligible = []
        for crop in self._by_canonical.values():
            pest_cfg = crop.get("pest_outbreak_prediction", {})
            if pest_cfg.get("eligible", False):
                if priority is None or pest_cfg.get("priority_tier") == priority:
                    eligible.append(crop)
        return eligible

    def get_pest_specification(self, name: str) -> dict[str, Any] | None:
        """Get pest species, thresholds, weather and historical data requirements for a crop."""
        crop = self.get_crop(name)
        if not crop:
            return None
        return {
            "canonical_id": crop["canonical_id"],
            "display_name": crop["display_name"],
            "category": crop["category"],
            "pest_outbreak_prediction": crop.get("pest_outbreak_prediction", {}),
            "pest_outbreak_preview": crop.get("models", {}).get("pest_outbreak_preview", {}),
        }


@lru_cache(maxsize=1)
def get_crop_catalog(path: str | None = None) -> CropCatalog:
    """Singleton cached provider for the central crop catalog."""
    catalog_path = Path(path) if path else DEFAULT_CATALOG_PATH
    return CropCatalog(catalog_path)
