"""
backend/ml/model_registry.py
─────────────────────────────
Robust, atomic model registry, validation gate, promotion, and rollback manager.
Guarantees atomic file updates, versioned backups, metric comparisons, and SHA-256 integrity.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_MIN_MACRO_F1 = 0.90


class PromotionError(ValueError):
    """Raised when a candidate model fails validation gates or does not beat production."""


class RollbackError(RuntimeError):
    """Raised when a rollback operation fails or target backup is invalid."""


class PromotionLock:
    """Process-level lock file preventing concurrent promotion race conditions."""

    def __init__(self, lock_path: Path, timeout: float = 10.0):
        self.lock_path = lock_path
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self):
        start = time.time()
        while True:
            try:
                self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                if time.time() - start > self.timeout:
                    # Check for stale lock (> 60 seconds old)
                    try:
                        mtime = self.lock_path.stat().st_mtime
                        if time.time() - mtime > 60:
                            LOGGER.warning("Removing stale promotion lock file: %s", self.lock_path)
                            self.lock_path.unlink(missing_ok=True)
                            continue
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Could not acquire promotion lock: '{self.lock_path}' is held by another process."
                    )
                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
            try:
                self.lock_path.unlink(missing_ok=True)
            except Exception:
                pass


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ledger_path(artifact_dir: str | Path) -> Path:
    return Path(artifact_dir) / "deployment_ledger.json"


def _lock_path(artifact_dir: str | Path) -> Path:
    return Path(artifact_dir) / ".promotion.lock"


def _backups_dir(artifact_dir: str | Path) -> Path:
    return Path(artifact_dir) / "backups"


def _candidates_dir(artifact_dir: str | Path) -> Path:
    return Path(artifact_dir) / "candidates"


def read_ledger(artifact_dir: str | Path) -> dict[str, Any]:
    path = _ledger_path(artifact_dir)
    if not path.exists():
        return {
            "production_version": None,
            "production_macro_f1": None,
            "production_sha256": None,
            "last_promoted_at": None,
            "history": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _write_ledger(artifact_dir: str | Path, ledger: dict[str, Any]) -> None:
    path = _ledger_path(artifact_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def validate_candidate(
    candidate_metadata: dict[str, Any],
    candidate_joblib_path: str | Path | None = None,
    current_ledger: dict[str, Any] | None = None,
    min_macro_f1: float = DEFAULT_MIN_MACRO_F1,
    min_macro_f1_improvement: float = 0.0,
) -> tuple[bool, str]:
    """
    Validate a candidate model against minimum criteria and current production benchmark.
    Returns (is_valid, reason).
    """
    version = candidate_metadata.get("model_version")
    if not version:
        return False, "Candidate metadata missing 'model_version'"

    # Synthetic / Experimental production isolation check
    classification = str(candidate_metadata.get("classification", ""))
    if "SYNTHETIC" in classification or candidate_metadata.get("is_production_ready") is False:
        return False, "Promotion rejected: Synthetic-data-trained models cannot be promoted to production"

    metrics = candidate_metadata.get("evaluation_metrics", {})
    if "macro_f1" not in metrics:
        return False, "Candidate metadata missing 'evaluation_metrics.macro_f1'"

    candidate_f1 = float(metrics["macro_f1"])
    if candidate_f1 < min_macro_f1:
        return False, f"Candidate macro F1 {candidate_f1:.4f} is below minimum requirement {min_macro_f1:.4f}"

    if candidate_joblib_path is not None:
        c_path = Path(candidate_joblib_path)
        if not c_path.exists() or c_path.stat().st_size == 0:
            return False, f"Candidate artifact file {c_path} is missing or empty"

        # Check candidate checksum integrity if recorded in metadata
        expected_sha = candidate_metadata.get("artifact_sha256")
        if expected_sha:
            actual_sha = sha256_file(c_path)
            if actual_sha != expected_sha:
                return False, f"Candidate checksum mismatch (expected: {expected_sha}, computed: {actual_sha})"

    if current_ledger:
        deployed_f1 = current_ledger.get("production_macro_f1")
        if deployed_f1 is not None:
            required_f1 = float(deployed_f1) + min_macro_f1_improvement
            if candidate_f1 < required_f1:
                return False, (
                    f"Candidate macro F1 {candidate_f1:.4f} does not meet required improvement "
                    f"(current production: {deployed_f1:.4f}, required: {required_f1:.4f})"
                )

    return True, f"Candidate {version} passed validation (macro F1: {candidate_f1:.4f})"


def stage_candidate(
    artifact_dir: str | Path,
    candidate_pipeline: Any,
    candidate_metadata: dict[str, Any],
    evaluation_report_md: str | None = None,
) -> Path:
    """
    Safely stages a candidate in artifacts/candidates/<version>/ without touching production.
    Returns the candidate directory.
    """
    version = candidate_metadata["model_version"]
    c_dir = _candidates_dir(artifact_dir) / version
    c_dir.mkdir(parents=True, exist_ok=True)

    import joblib
    model_file = c_dir / "crop_model.joblib"
    joblib.dump(candidate_pipeline, model_file)

    checksum = sha256_file(model_file)
    # Store checksum in metadata so validation verifies it
    candidate_metadata["artifact_sha256"] = checksum

    meta_file = c_dir / "metadata.json"
    meta_file.write_text(json.dumps(candidate_metadata, indent=2), encoding="utf-8")

    if evaluation_report_md:
        (c_dir / "evaluation_report.md").write_text(evaluation_report_md, encoding="utf-8")

    (c_dir / "checksum.sha256").write_text(checksum, encoding="utf-8")

    LOGGER.info("Candidate %s staged in %s (sha256: %s)", version, c_dir, checksum[:12])
    return c_dir


def promote_candidate(
    artifact_dir: str | Path,
    candidate_metadata: dict[str, Any],
    candidate_source_dir: str | Path | None = None,
    min_macro_f1: float = DEFAULT_MIN_MACRO_F1,
    min_macro_f1_improvement: float = 0.0,
) -> dict[str, Any]:
    """
    Atomically promotes a candidate model into production (crop_model.joblib + metadata.json).
    Ensures:
      1. Candidate validation passes (minimum macro F1, improvement margin, checksums).
      2. Existing production model is backed up in backups/<version>/.
      3. Promotion is atomic via temporary files and os.replace().
      4. Deployment ledger is updated with SHA-256 and metrics.
      5. Process lock prevents concurrent promotion races.
    """
    art_dir = Path(artifact_dir)
    version = candidate_metadata["model_version"]

    with PromotionLock(_lock_path(art_dir)):
        ledger = read_ledger(art_dir)

        # Locate candidate files
        if candidate_source_dir:
            src_dir = Path(candidate_source_dir)
        else:
            src_dir = _candidates_dir(art_dir) / version
            if not src_dir.exists():
                src_dir = art_dir

        candidate_joblib = src_dir / "crop_model.joblib"
        candidate_report = src_dir / "evaluation_report.md"

        # Validate candidate
        is_valid, reason = validate_candidate(
            candidate_metadata=candidate_metadata,
            candidate_joblib_path=candidate_joblib,
            current_ledger=ledger,
            min_macro_f1=min_macro_f1,
            min_macro_f1_improvement=min_macro_f1_improvement,
        )
        if not is_valid:
            LOGGER.warning("Promotion rejected: %s", reason)
            raise PromotionError(reason)

        prod_joblib = art_dir / "crop_model.joblib"
        prod_meta = art_dir / "metadata.json"
        prod_report = art_dir / "evaluation_report.md"

        # Step 1: Backup current production model if it exists
        current_prod_version = ledger.get("production_version")
        if prod_joblib.exists() and current_prod_version:
            backup_dir = _backups_dir(art_dir) / current_prod_version
            backup_dir.mkdir(parents=True, exist_ok=True)
            if prod_joblib.resolve() != (backup_dir / "crop_model.joblib").resolve():
                shutil.copy2(prod_joblib, backup_dir / "crop_model.joblib")
            if prod_meta.exists() and prod_meta.resolve() != (backup_dir / "metadata.json").resolve():
                shutil.copy2(prod_meta, backup_dir / "metadata.json")
            if prod_report.exists() and prod_report.resolve() != (backup_dir / "evaluation_report.md").resolve():
                shutil.copy2(prod_report, backup_dir / "evaluation_report.md")
            LOGGER.info("Backed up production model %s to %s", current_prod_version, backup_dir)

        # Step 2: Atomic update to production files using temporary staging files
        candidate_f1 = float(candidate_metadata["evaluation_metrics"]["macro_f1"])
        candidate_sha = sha256_file(candidate_joblib)

        tmp_joblib = art_dir / "crop_model.joblib.tmp"
        tmp_meta = art_dir / "metadata.json.tmp"
        tmp_report = art_dir / "evaluation_report.md.tmp"

        try:
            shutil.copy2(candidate_joblib, tmp_joblib)

            promoted_meta = dict(candidate_metadata)
            promoted_meta["deployment_status"] = "production"
            promoted_meta["promoted_at"] = datetime.now(timezone.utc).isoformat()
            promoted_meta["artifact_sha256"] = candidate_sha
            tmp_meta.write_text(json.dumps(promoted_meta, indent=2), encoding="utf-8")

            if candidate_report.exists():
                shutil.copy2(candidate_report, tmp_report)
            else:
                tmp_report.write_text(f"# Evaluation Report - {version}\n", encoding="utf-8")

            # Atomic swap
            os.replace(tmp_joblib, prod_joblib)
            os.replace(tmp_meta, prod_meta)
            os.replace(tmp_report, prod_report)
        finally:
            # Clean up dangling tmp files if swap was interrupted
            for tmp in (tmp_joblib, tmp_meta, tmp_report):
                if tmp.exists():
                    tmp.unlink(missing_ok=True)

        # Step 3: Update ledger
        now_iso = datetime.now(timezone.utc).isoformat()
        ledger["production_version"] = version
        ledger["production_macro_f1"] = candidate_f1
        ledger["production_sha256"] = candidate_sha
        ledger["last_promoted_at"] = now_iso
        ledger.setdefault("history", []).append(
            {
                "action": "promote",
                "model_version": version,
                "macro_f1": candidate_f1,
                "sha256": candidate_sha,
                "previous_version": current_prod_version,
                "timestamp": now_iso,
            }
        )
        _write_ledger(art_dir, ledger)
        LOGGER.info("Successfully promoted candidate %s to production (macro F1: %.4f)", version, candidate_f1)
        return ledger


def rollback(
    artifact_dir: str | Path,
    target_version: str | None = None,
) -> dict[str, Any]:
    """
    Physically rolls back the production model to target_version (or previous deployed version).
    Restores the actual .joblib binary and metadata.json atomically from backups.
    """
    art_dir = Path(artifact_dir)

    with PromotionLock(_lock_path(art_dir)):
        ledger = read_ledger(art_dir)
        current_version = ledger.get("production_version")

        # Determine target version from history if not supplied
        if not target_version:
            history = ledger.get("history", [])
            # Look backwards for the most recent version that is not the current version
            candidates = [h for h in reversed(history) if h.get("model_version") != current_version]
            if not candidates:
                raise RollbackError("No prior model version found in deployment ledger history to rollback to.")
            target_version = candidates[0]["model_version"]

        # Search for backup files in backups/ or candidates/
        target_backup_dir = _backups_dir(art_dir) / target_version
        if not target_backup_dir.exists():
            target_backup_dir = _candidates_dir(art_dir) / target_version

        if not target_backup_dir.exists():
            raise RollbackError(f"Backup artifacts for version '{target_version}' not found in {art_dir}")

        target_joblib = target_backup_dir / "crop_model.joblib"
        target_meta = target_backup_dir / "metadata.json"
        if not target_joblib.exists() or not target_meta.exists():
            raise RollbackError(f"Missing required rollback files in {target_backup_dir}")

        prod_joblib = art_dir / "crop_model.joblib"
        prod_meta = art_dir / "metadata.json"
        prod_report = art_dir / "evaluation_report.md"

        # Backup current production before rolling back
        if prod_joblib.exists() and current_version:
            curr_backup = _backups_dir(art_dir) / current_version
            curr_backup.mkdir(parents=True, exist_ok=True)
            if prod_joblib.resolve() != (curr_backup / "crop_model.joblib").resolve():
                shutil.copy2(prod_joblib, curr_backup / "crop_model.joblib")
            if prod_meta.exists() and prod_meta.resolve() != (curr_backup / "metadata.json").resolve():
                shutil.copy2(prod_meta, curr_backup / "metadata.json")

        # Atomically restore target
        tmp_joblib = art_dir / "crop_model.joblib.tmp"
        tmp_meta = art_dir / "metadata.json.tmp"
        tmp_report = art_dir / "evaluation_report.md.tmp"

        try:
            shutil.copy2(target_joblib, tmp_joblib)
            shutil.copy2(target_meta, tmp_meta)

            target_report = target_backup_dir / "evaluation_report.md"
            if target_report.exists():
                shutil.copy2(target_report, tmp_report)
                os.replace(tmp_report, prod_report)

            os.replace(tmp_joblib, prod_joblib)
            os.replace(tmp_meta, prod_meta)
        finally:
            for tmp in (tmp_joblib, tmp_meta, tmp_report):
                if tmp.exists():
                    tmp.unlink(missing_ok=True)

        # Read restored metadata
        restored_meta = json.loads(target_meta.read_text(encoding="utf-8"))
        restored_f1 = float(restored_meta.get("evaluation_metrics", {}).get("macro_f1", 0.0))
        restored_sha = sha256_file(prod_joblib)

        now_iso = datetime.now(timezone.utc).isoformat()
        ledger["production_version"] = target_version
        ledger["production_macro_f1"] = restored_f1
        ledger["production_sha256"] = restored_sha
        ledger["last_promoted_at"] = now_iso
        ledger.setdefault("history", []).append(
            {
                "action": "rollback",
                "model_version": target_version,
                "macro_f1": restored_f1,
                "sha256": restored_sha,
                "previous_version": current_version,
                "timestamp": now_iso,
            }
        )
        _write_ledger(art_dir, ledger)
        LOGGER.info("Physical rollback complete: restored version %s to production (macro F1: %.4f)", target_version, restored_f1)
        return ledger


# ─────────────────────────────────────────────────────────────────────────────
# Pest Forecasting Model Registry (Experimental Tier with Strict Isolation)
# ─────────────────────────────────────────────────────────────────────────────

PEST_LEDGER_FILENAME = "pest_deployment_ledger.json"
PEST_PIPELINE_FILES = (
    "environmental_model_pipeline.joblib",
    "full_model_pipeline.joblib",
)
PEST_METADATA_FILES = (
    "feature_schemas.json",
    "model_config.json",
    "partition_metadata.json",
    "synthetic_provenance_metadata.json",
    "stress_test_results.json",
    "experiment_comparison_summary.json",
    "inference_examples.json",
)


def _pest_ledger_path(models_dir: str | Path) -> Path:
    return Path(models_dir) / PEST_LEDGER_FILENAME


def read_pest_ledger(models_dir: str | Path) -> dict[str, Any]:
    path = _pest_ledger_path(models_dir)
    if not path.exists():
        return {
            "active_experimental_version": None,
            "active_val_pr_auc": None,
            "active_checksums": {},
            "last_promoted_at": None,
            "tier": "experimental",
            "history": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _write_pest_ledger(models_dir: str | Path, ledger: dict[str, Any]) -> None:
    path = _pest_ledger_path(models_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def validate_pest_candidate(
    candidate_metadata: dict[str, Any],
    candidate_dir: str | Path | None = None,
    current_ledger: dict[str, Any] | None = None,
    min_val_pr_auc: float = 0.50,
    target_tier: str = "experimental",
) -> tuple[bool, str]:
    """
    Validate a pest forecasting candidate against scientific criteria,
    checksum integrity, and strict production isolation guarantees.
    """
    version = candidate_metadata.get("model_version")
    if not version:
        return False, "Candidate metadata missing 'model_version'"

    # 1. Strict Production Isolation Gate
    if target_tier == "production":
        classification = str(candidate_metadata.get("classification", ""))
        is_ready = candidate_metadata.get("is_production_ready", False)
        if "SYNTHETIC" in classification or not is_ready:
            return False, (
                "Promotion to PRODUCTION strictly BLOCKED: Synthetic-data-trained models are "
                "restricted to the experimental tier. Authentic ground-truth field surveillance required."
            )
        try:
            from src.pest_risk.production_readiness_gate import evaluate_production_readiness
            report = evaluate_production_readiness()
            if not report.is_ready_for_training:
                return False, (
                    f"Promotion to PRODUCTION strictly BLOCKED by scientific readiness gate: "
                    f"{len(report.blocking_reasons)} blocking gates pending."
                )
        except Exception as exc:
            return False, f"Scientific readiness gate check failed: {exc}"

    # 2. Extract validation PR-AUC metric
    val_pr_auc = candidate_metadata.get("best_val_pr_auc")
    if val_pr_auc is None:
        # Check nested experiments structure
        exps = candidate_metadata.get("experiments", {})
        if "ENVIRONMENTAL_ONLY" in exps:
            val_pr_auc = exps["ENVIRONMENTAL_ONLY"].get("best_val_pr_auc")
        elif "SCOUTING_ASSISTED" in exps:
            val_pr_auc = exps["SCOUTING_ASSISTED"].get("best_val_pr_auc")

    if val_pr_auc is None:
        return False, "Candidate metadata missing validation PR-AUC metric"

    val_pr_auc = float(val_pr_auc)
    if val_pr_auc < min_val_pr_auc:
        return False, f"Candidate validation PR-AUC {val_pr_auc:.4f} is below minimum requirement {min_val_pr_auc:.4f}"

    # 3. Check artifact files and SHA-256 integrity if directory supplied
    if candidate_dir:
        c_path = Path(candidate_dir)
        for pipe_name in PEST_PIPELINE_FILES:
            pipe_file = c_path / pipe_name
            if not pipe_file.exists() or pipe_file.stat().st_size == 0:
                return False, f"Required candidate pipeline file missing or empty: {pipe_file}"

        recorded_checksums = candidate_metadata.get("artifact_checksums", {})
        for fname, expected_sha in recorded_checksums.items():
            f_file = c_path / fname
            if f_file.exists():
                actual_sha = sha256_file(f_file)
                if actual_sha != expected_sha:
                    return False, f"Candidate checksum mismatch for {fname} (expected {expected_sha}, computed {actual_sha})"

    # 4. Check improvement against current active experimental baseline
    if current_ledger:
        active_pr_auc = current_ledger.get("active_val_pr_auc")
        if active_pr_auc is not None and val_pr_auc < float(active_pr_auc):
            return False, (
                f"Candidate PR-AUC {val_pr_auc:.4f} is inferior to current active baseline {float(active_pr_auc):.4f}"
            )

    return True, f"Candidate {version} passed validation (val PR-AUC: {val_pr_auc:.4f})"


def stage_pest_candidate(
    models_dir: str | Path,
    version: str,
    candidate_metadata: dict[str, Any],
    pipelines: dict[str, Any] | None = None,
    source_artifacts_dir: str | Path | None = None,
) -> Path:
    """
    Stages an experimental pest forecasting candidate under models_dir/candidates/<version>/.
    Saves or copies pipelines and metadata files, calculates and records SHA-256 checksums.
    """
    m_dir = Path(models_dir)
    c_dir = m_dir / "candidates" / version
    c_dir.mkdir(parents=True, exist_ok=True)

    import joblib

    # 1. Save or copy pipeline binaries
    if pipelines:
        if "environmental_pipeline" in pipelines:
            joblib.dump(pipelines["environmental_pipeline"], c_dir / "environmental_model_pipeline.joblib")
        if "full_pipeline" in pipelines:
            joblib.dump(pipelines["full_pipeline"], c_dir / "full_model_pipeline.joblib")

    if source_artifacts_dir:
        s_dir = Path(source_artifacts_dir)
        for fname in PEST_PIPELINE_FILES + PEST_METADATA_FILES:
            src_f = s_dir / fname
            dst_f = c_dir / fname
            if src_f.exists() and not dst_f.exists():
                shutil.copy2(src_f, dst_f)

    # 2. Compute SHA-256 for all artifacts present in candidate dir
    checksums: dict[str, str] = {}
    for f in c_dir.iterdir():
        if f.is_file() and f.name != "checksums.sha256" and f.name != "candidate_metadata.json":
            checksums[f.name] = sha256_file(f)

    checksum_lines = [f"{sha}  {fname}" for fname, sha in sorted(checksums.items())]
    (c_dir / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    # 3. Update candidate metadata with version and checksums
    candidate_metadata["model_version"] = version
    candidate_metadata["artifact_checksums"] = checksums
    candidate_metadata["staged_at"] = datetime.now(timezone.utc).isoformat()
    (c_dir / "candidate_metadata.json").write_text(json.dumps(candidate_metadata, indent=2), encoding="utf-8")

    LOGGER.info("Staged pest candidate %s in %s (%d artifacts verified)", version, c_dir, len(checksums))
    return c_dir


def promote_pest_experimental_candidate(
    models_dir: str | Path,
    candidate_metadata: dict[str, Any],
    candidate_source_dir: str | Path | None = None,
    min_val_pr_auc: float = 0.50,
    target_tier: str = "experimental",
) -> dict[str, Any]:
    """
    Promotes a candidate pest forecasting model to the active experimental baseline.
    Strictly prohibits promotion to production when trained on synthetic data.
    Backs up previous active experimental models to models_dir/backups/<prev_version>/.
    """
    m_dir = Path(models_dir)
    version = candidate_metadata["model_version"]

    with PromotionLock(_lock_path(m_dir)):
        ledger = read_pest_ledger(m_dir)

        if candidate_source_dir:
            src_dir = Path(candidate_source_dir)
        else:
            src_dir = m_dir / "candidates" / version
            if not src_dir.exists():
                src_dir = m_dir

        # Validate candidate
        is_valid, reason = validate_pest_candidate(
            candidate_metadata=candidate_metadata,
            candidate_dir=src_dir,
            current_ledger=ledger,
            min_val_pr_auc=min_val_pr_auc,
            target_tier=target_tier,
        )
        if not is_valid:
            LOGGER.warning("Pest model promotion rejected: %s", reason)
            raise PromotionError(reason)

        # Step 1: Backup current active experimental model if one was active
        curr_version = ledger.get("active_experimental_version")
        if curr_version:
            backup_dir = m_dir / "backups" / curr_version
            backup_dir.mkdir(parents=True, exist_ok=True)
            for fname in PEST_PIPELINE_FILES + PEST_METADATA_FILES:
                src_file = m_dir / fname
                if src_file.exists():
                    shutil.copy2(src_file, backup_dir / fname)
            LOGGER.info("Backed up prior experimental version %s to %s", curr_version, backup_dir)

        # Step 2: Atomic update to active files in models_dir
        tmp_files: list[Path] = []
        try:
            for fname in PEST_PIPELINE_FILES + PEST_METADATA_FILES:
                cand_file = src_dir / fname
                if cand_file.exists():
                    tmp_f = m_dir / f"{fname}.tmp"
                    shutil.copy2(cand_file, tmp_f)
                    tmp_files.append(tmp_f)

            # Atomic replace
            for tmp_f in tmp_files:
                target_f = m_dir / tmp_f.name.replace(".tmp", "")
                os.replace(tmp_f, target_f)
        finally:
            for tmp_f in tmp_files:
                if tmp_f.exists():
                    tmp_f.unlink(missing_ok=True)

        # Step 3: Compute promoted checksums and update ledger
        promoted_checksums = {}
        for fname in PEST_PIPELINE_FILES:
            fpath = m_dir / fname
            if fpath.exists():
                promoted_checksums[fname] = sha256_file(fpath)

        now_iso = datetime.now(timezone.utc).isoformat()
        val_pr_auc = float(candidate_metadata.get("best_val_pr_auc", 0.0))
        if val_pr_auc == 0.0 and "experiments" in candidate_metadata:
            val_pr_auc = float(candidate_metadata["experiments"]["ENVIRONMENTAL_ONLY"].get("best_val_pr_auc", 0.0))

        ledger["active_experimental_version"] = version
        ledger["active_val_pr_auc"] = val_pr_auc
        ledger["active_checksums"] = promoted_checksums
        ledger["last_promoted_at"] = now_iso
        ledger.setdefault("history", []).append(
            {
                "action": "promote_experimental",
                "model_version": version,
                "val_pr_auc": val_pr_auc,
                "checksums": promoted_checksums,
                "previous_version": curr_version,
                "timestamp": now_iso,
            }
        )
        _write_pest_ledger(m_dir, ledger)
        LOGGER.info("Promoted pest candidate %s to active experimental (val PR-AUC: %.4f)", version, val_pr_auc)
        return ledger


def rollback_pest_experimental(
    models_dir: str | Path,
    target_version: str | None = None,
) -> dict[str, Any]:
    """
    Physically rolls back the experimental pest forecasting models to target_version
    from models_dir/backups/ or models_dir/candidates/.
    """
    m_dir = Path(models_dir)

    with PromotionLock(_lock_path(m_dir)):
        ledger = read_pest_ledger(m_dir)
        curr_version = ledger.get("active_experimental_version")

        if not target_version:
            history = ledger.get("history", [])
            candidates = [h for h in reversed(history) if h.get("model_version") != curr_version]
            if not candidates:
                raise RollbackError("No prior pest model version found in experimental ledger history to rollback to.")
            target_version = candidates[0]["model_version"]

        target_backup_dir = m_dir / "backups" / target_version
        if not target_backup_dir.exists():
            target_backup_dir = m_dir / "candidates" / target_version

        if not target_backup_dir.exists():
            raise RollbackError(f"Backup artifacts for pest version '{target_version}' not found in {m_dir}")

        # Check required files in backup
        for fname in PEST_PIPELINE_FILES:
            if not (target_backup_dir / fname).exists():
                raise RollbackError(f"Missing required pipeline file in backup {target_backup_dir}: {fname}")

        # Backup current state before restoring
        if curr_version:
            curr_backup = m_dir / "backups" / curr_version
            curr_backup.mkdir(parents=True, exist_ok=True)
            for fname in PEST_PIPELINE_FILES + PEST_METADATA_FILES:
                src_f = m_dir / fname
                if src_f.exists() and src_f.resolve() != (curr_backup / fname).resolve():
                    shutil.copy2(src_f, curr_backup / fname)

        # Atomically restore
        tmp_files: list[Path] = []
        try:
            for fname in PEST_PIPELINE_FILES + PEST_METADATA_FILES:
                src_f = target_backup_dir / fname
                if src_f.exists():
                    tmp_f = m_dir / f"{fname}.tmp"
                    shutil.copy2(src_f, tmp_f)
                    tmp_files.append(tmp_f)

            for tmp_f in tmp_files:
                target_f = m_dir / tmp_f.name.replace(".tmp", "")
                os.replace(tmp_f, target_f)
        finally:
            for tmp_f in tmp_files:
                if tmp_f.exists():
                    tmp_f.unlink(missing_ok=True)

        restored_checksums = {}
        for fname in PEST_PIPELINE_FILES:
            fpath = m_dir / fname
            if fpath.exists():
                restored_checksums[fname] = sha256_file(fpath)

        now_iso = datetime.now(timezone.utc).isoformat()
        ledger["active_experimental_version"] = target_version
        ledger["active_checksums"] = restored_checksums
        ledger["last_promoted_at"] = now_iso
        ledger.setdefault("history", []).append(
            {
                "action": "rollback_experimental",
                "model_version": target_version,
                "checksums": restored_checksums,
                "previous_version": curr_version,
                "timestamp": now_iso,
            }
        )
        _write_pest_ledger(m_dir, ledger)
        LOGGER.info("Physical rollback complete: restored pest version %s to active experimental", target_version)
        return ledger
