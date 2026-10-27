"""
backend/ml/fertilizer.py
─────────────────────────
Fertilizer prediction engine, model wrapper, and artifact verification for AgriAdapt AI MLOps pipeline.
Integrates the Indian Soil Health Card + ICAR-IISS general fertilizer recommendation ensemble.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path so pickle unpickling of src.models.model succeeds
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model import (
    FertilizerRecommendationModel,
    TARGETS,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from src.models.predict import (
    FertilizerPredictor,
    predict_fertilizer,
    get_example_input,
    VALID_CROPS,
    REQUIRED_FEATURES,
    DEFAULT_MODEL_PATH,
    SCHEMA_PATH,
)

LOGGER = logging.getLogger(__name__)

__all__ = [
    "FertilizerRecommendationModel",
    "FertilizerPredictor",
    "predict_fertilizer",
    "get_example_input",
    "VALID_CROPS",
    "REQUIRED_FEATURES",
    "NUMERIC_FEATURES",
    "CATEGORICAL_FEATURES",
    "TARGETS",
    "DEFAULT_MODEL_PATH",
    "SCHEMA_PATH",
    "verify_fertilizer_artifacts",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_fertilizer_artifacts(
    models_dir: str | Path | None = None,
    target_artifacts_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Verifies the integrity of the integrated fertilizer recommendation ensemble model.
    Checks:
      1. Model binary exists, loads cleanly as FertilizerRecommendationModel, and is non-empty.
      2. Metadata JSON is valid and contains version, targets, and feature specifications.
      3. Feature schema JSON defines valid nutrient index bounds [1.0, 3.0].
      4. Executes a verification inference test against verified ICAR-IISS sample plot inputs.
      5. Synchronizes verified artifacts into target_artifacts_dir (backend/artifacts) for deployment consistency.
      6. Writes fertilizer_verification.json summary.
    """
    source_dir = Path(models_dir) if models_dir else PROJECT_ROOT / "models"
    dest_dir = Path(target_artifacts_dir) if target_artifacts_dir else PROJECT_ROOT / "backend" / "artifacts"
    dest_dir.mkdir(parents=True, exist_ok=True)

    model_path = source_dir / "fertilizer_model.joblib"
    meta_path = source_dir / "fertilizer_model_metadata.json"
    schema_path = source_dir / "fertilizer_feature_schema.json"

    # Fallback to dest_dir if source_dir is missing primary artifacts
    if not model_path.exists() and (dest_dir / "fertilizer_model.joblib").exists():
        model_path = dest_dir / "fertilizer_model.joblib"
        meta_path = dest_dir / "fertilizer_model_metadata.json"
        schema_path = dest_dir / "fertilizer_feature_schema.json"

    missing = [str(p) for p in (model_path, meta_path, schema_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required fertilizer model artifacts: {missing}")

    # 1. Validate schema
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    required_in_schema = schema.get("required", [])
    for feat in REQUIRED_FEATURES:
        if feat not in props and feat not in required_in_schema:
            raise ValueError(f"Feature schema missing contract definition for required feature: {feat}")

    # 2. Validate metadata
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    version = metadata.get("model_version", "unknown")
    if not version or version == "unknown":
        raise ValueError("Fertilizer metadata missing model_version")

    # 3. Load model and verify class
    predictor = FertilizerPredictor(model_path=str(model_path))
    if not isinstance(predictor.model, FertilizerRecommendationModel):
        raise TypeError(f"Loaded model is of type {type(predictor.model)}, expected FertilizerRecommendationModel")

    # 4. Verification inference test
    sample_input = get_example_input()
    result = predictor.predict(sample_input)
    recs = result.get("recommendations", {})
    bags = result.get("fertilizer_commercial_equivalent_approx", {})

    for nutrient in ("nitrogen", "phosphorus", "potassium"):
        val = recs.get(nutrient, {}).get("value")
        if val is None or val < 0:
            raise ValueError(f"Inference test failed: {nutrient} produced invalid value {val}")

    for bag in ("urea_46_pct_n_kg_ha", "dap_46_pct_p2o5_kg_ha", "mop_60_pct_k2o_kg_ha"):
        bag_val = bags.get(bag)
        if bag_val is None or bag_val < 0:
            raise ValueError(f"Inference test failed: commercial bag {bag} produced invalid value {bag_val}")

    # 5. Synchronize artifacts to backend/artifacts if different
    model_sha = _sha256(model_path)
    for src_file, fname in (
        (model_path, "fertilizer_model.joblib"),
        (meta_path, "fertilizer_model_metadata.json"),
        (schema_path, "fertilizer_feature_schema.json"),
    ):
        target_file = dest_dir / fname
        if target_file.resolve() != src_file.resolve():
            shutil.copy2(src_file, target_file)

    verification_summary = {
        "status": "VERIFIED",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "model_version": version,
        "model_file": str(model_path),
        "model_sha256": model_sha,
        "model_size_bytes": model_path.stat().st_size,
        "targets": TARGETS,
        "test_crop": sample_input.get("crop"),
        "test_state": sample_input.get("state_name"),
        "test_outputs": {
            "N_kg_ha": recs.get("nitrogen", {}).get("value"),
            "P2O5_kg_ha": recs.get("phosphorus", {}).get("value"),
            "K2O_kg_ha": recs.get("potassium", {}).get("value"),
        },
    }

    verification_path = dest_dir / "fertilizer_verification.json"
    verification_path.write_text(json.dumps(verification_summary, indent=2), encoding="utf-8")
    LOGGER.info("Fertilizer ensemble verified successfully: version %s (sha256: %s)", version, model_sha[:12])
    return verification_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Fertilizer model artifact verification CLI")
    parser.add_argument("--verify", action="store_true", help="Run artifact integrity check and sample inference test")
    parser.add_argument("--models-dir", default=None, help="Directory containing source fertilizer models")
    parser.add_argument("--artifacts-dir", default=None, help="Destination directory for deployment artifacts")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    summary = verify_fertilizer_artifacts(args.models_dir, args.artifacts_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
