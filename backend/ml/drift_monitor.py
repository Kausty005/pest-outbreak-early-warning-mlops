"""Evidently AI and Kolmogorov-Smirnov drift monitor for AgriAdapt crop model inputs.

Distinguishes genuine production-log monitoring from synthetic demonstration runs,
handles malformed or small-sample logs safely, and reports data source provenance.
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
FEATURE_COLUMNS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
DEFAULT_DRIFT_THRESHOLD = 0.30  # fraction of drifted features that triggers an alert


def load_reference_data(dataset_path: str | Path) -> pd.DataFrame:
    """Load training reference dataset, return only feature columns."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Reference dataset not found: {path}")
    df = pd.read_csv(path)
    missing = [f for f in FEATURE_COLUMNS if f not in df.columns]
    if missing:
        raise ValueError(f"Reference dataset missing columns: {missing}")
    return df[FEATURE_COLUMNS]


def _synthetic_drift_sample(n: int = 200) -> pd.DataFrame:
    """Generate a synthetic batch that simulates moderate input drift (warmer / wetter)."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "N":           rng.normal(100, 25, n).clip(0, 300),
        "P":           rng.normal(55,  20, n).clip(0, 300),
        "K":           rng.normal(60,  20, n).clip(0, 400),
        "temperature": rng.normal(32,   5, n).clip(-10, 60),  # shifted +5°C vs training
        "humidity":    rng.normal(75,  12, n).clip(0, 100),
        "ph":          rng.normal(6.8, 0.8, n).clip(0, 14),
        "rainfall":    rng.normal(120, 60, n).clip(0, 1000),
    })
    df.attrs["data_source"] = "synthetic_demonstration"
    df.attrs["is_synthetic"] = True
    return df


def load_prediction_log(
    log_path: str | Path,
    allow_synthetic: bool = True,
    min_samples: int = 1,
) -> pd.DataFrame:
    """
    Load logged prediction inputs from a JSONL file.
    Safely ignores malformed records.
    If logs are empty or missing:
      - If allow_synthetic=True: returns labeled synthetic drift batch.
      - If allow_synthetic=False: raises ValueError explaining insufficient samples.
    """
    path = Path(log_path)
    if not path.exists() or path.stat().st_size == 0:
        if not allow_synthetic:
            raise ValueError(
                f"Prediction log at '{path}' is empty or does not exist. "
                f"Insufficient production samples (found 0, minimum {min_samples} required)."
            )
        LOGGER.info("No prediction log at %s — using labeled synthetic demonstration batch", path)
        return _synthetic_drift_sample()

    records = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as err:
            LOGGER.warning("Skipping malformed JSON line %d in %s: %s", idx, path, err)

    if not records or len(records) < min_samples:
        if not allow_synthetic:
            raise ValueError(
                f"Prediction log at '{path}' contains {len(records)} valid records, "
                f"which is below the minimum required sample size of {min_samples}."
            )
        LOGGER.info("Prediction log has insufficient records (%d < %d) — using synthetic demonstration batch", len(records), min_samples)
        return _synthetic_drift_sample()

    raw_df = pd.DataFrame(records)
    common_cols = [c for c in FEATURE_COLUMNS if c in raw_df.columns]
    if not common_cols:
        if not allow_synthetic:
            raise ValueError(f"Prediction log at '{path}' contains none of the required features: {FEATURE_COLUMNS}")
        return _synthetic_drift_sample()

    df = raw_df[common_cols].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if len(df) < min_samples:
        if not allow_synthetic:
            raise ValueError(f"After filtering numeric features, only {len(df)} records remained (< {min_samples}).")
        return _synthetic_drift_sample()

    df.attrs["data_source"] = "production_logs"
    df.attrs["is_synthetic"] = False
    return df


def run_drift_detection(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    report_dir: str | Path = "logs/drift",
    run_id: str | None = None,
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
    data_source: str | None = None,
) -> dict[str, Any]:
    """
    Run Evidently DataDriftPreset or Kolmogorov-Smirnov 2-sample statistical tests.
    Generates HTML report and structured JSON summary with data source provenance.
    """
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc)
    run_id = run_id or ts.strftime("%Y%m%dT%H%M%SZ")

    source_label = data_source or getattr(current, "attrs", {}).get("data_source", "production_logs")
    is_synthetic = bool((source_label == "synthetic_demonstration") or getattr(current, "attrs", {}).get("is_synthetic", False))

    common_cols = [c for c in FEATURE_COLUMNS if c in reference.columns and c in current.columns]
    ref = reference[common_cols].reset_index(drop=True)
    cur = current[common_cols].reset_index(drop=True)

    html_path = report_dir / f"drift_report_{run_id}.html"

    summary: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": ts.isoformat(),
        "data_source": source_label,
        "is_synthetic": is_synthetic,
        "reference_rows": len(ref),
        "current_rows": len(cur),
        "features_checked": common_cols,
        "drift_threshold": round(float(threshold), 3),
        "html_report": str(html_path),
        "feature_drift": {},
        "drift_detected": False,
        "drifted_feature_count": 0,
        "drift_share": 0.0,
        "alert": False,
        "performance_degradation_measured": False,
        "performance_degradation_note": (
            "Actual model predictive performance degradation cannot be computed "
            "because true ground-truth post-harvest outcomes are not available in production input stream."
        ),
    }

    use_evidently = True
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset

        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref, current_data=cur)
        report.save_html(str(html_path))
        LOGGER.info("Evidently drift HTML report: %s", html_path)
        report_dict = report.as_dict()

        for metric in report_dict.get("metrics", []):
            result = metric.get("result", {})
            for col, stats in result.get("drift_by_columns", {}).items():
                summary["feature_drift"][col] = {
                    "drift_detected": bool(stats.get("drift_detected", False)),
                    "stattest": stats.get("stattest_name", ""),
                    "p_value": stats.get("p_value"),
                    "drift_score": stats.get("drift_score"),
                }
            if "share_of_drifted_columns" in result:
                summary["drift_share"] = float(result["share_of_drifted_columns"])
                summary["drift_detected"] = bool(result.get("dataset_drift", False))
            if "number_of_drifted_columns" in result:
                summary["drifted_feature_count"] = int(result["number_of_drifted_columns"])

    except Exception as exc:  # noqa: BLE001
        LOGGER.info("Using scipy Kolmogorov-Smirnov 2-sample drift engine (Evidently note: %s)", exc)
        use_evidently = False
        from scipy import stats

        drifted_count = 0
        html_rows = []
        for col in common_cols:
            ref_series = ref[col].dropna()
            cur_series = cur[col].dropna()

            # Handle empty or constant columns safely
            if len(ref_series) == 0 or len(cur_series) == 0:
                is_drifted = False
                stat_val = 0.0
                pval = 1.0
            elif ref_series.nunique() <= 1 and cur_series.nunique() <= 1:
                is_drifted = bool(ref_series.iloc[0] != cur_series.iloc[0])
                stat_val = 1.0 if is_drifted else 0.0
                pval = 0.0 if is_drifted else 1.0
            else:
                res = stats.ks_2samp(ref_series, cur_series)
                stat_val = float(res.statistic)
                pval = float(res.pvalue)
                is_drifted = bool(pval < 0.05)

            if is_drifted:
                drifted_count += 1

            summary["feature_drift"][col] = {
                "drift_detected": is_drifted,
                "stattest": "Kolmogorov-Smirnov (alpha=0.05)",
                "p_value": round(pval, 6),
                "drift_score": round(stat_val, 4),
            }
            status_badge = "<span style='color: #ef4444; font-weight: bold;'>DRIFT</span>" if is_drifted else "<span style='color: #22c55e;'>STABLE</span>"
            html_rows.append(f"<tr><td><b>{col}</b></td><td>{stat_val:.4f}</td><td>{pval:.4e}</td><td>{status_badge}</td></tr>")

        summary["drifted_feature_count"] = drifted_count
        summary["drift_share"] = round(drifted_count / len(common_cols), 4) if common_cols else 0.0
        summary["drift_detected"] = summary["drift_share"] >= threshold

        source_badge = (
            "<span style='background: #eab30833; color: #facc15; padding: 4px 10px; border-radius: 12px; font-weight: 700; border: 1px solid #eab308;'>"
            "SYNTHETIC DEMONSTRATION (SIMULATED SHIFT)</span>"
            if is_synthetic
            else "<span style='background: #22c55e33; color: #4ade80; padding: 4px 10px; border-radius: 12px; font-weight: 700; border: 1px solid #22c55e;'>"
            "GENUINE PRODUCTION LOGS</span>"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>AgriAdapt Data Drift Report - {run_id}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #0f172a; color: #f8fafc; }}
    h1 {{ color: #38bdf8; font-size: 24px; }}
    .summary-card {{ background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 24px; border: 1px solid #334155; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: #1e293b; border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #334155; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
  </style>
</head>
<body>
  <h1>🌾 AgriAdapt Model Input Drift Report</h1>
  <div class="summary-card">
    <p><b>Run ID:</b> {run_id} | <b>Timestamp:</b> {ts.isoformat()}</p>
    <p><b>Data Source Provenance:</b> {source_badge}</p>
    <p><b>Reference Rows:</b> {len(ref)} | <b>Current Rows:</b> {len(cur)}</p>
    <p><b>Drift Threshold:</b> {threshold*100:.0f}% feature drift trigger</p>
    <p><b>Drift Status:</b> {'⚠️ ALERT - DRIFT THRESHOLD EXCEEDED' if summary['drift_share'] >= threshold else '✅ STABLE / HEALTHY'}</p>
    <p><b>Drifted Features:</b> {drifted_count} / {len(common_cols)} ({summary['drift_share']*100:.1f}%)</p>
    <p style="color: #94a3b8; font-size: 12px; margin-top: 10px;"><i>Note: This monitors feature distribution shift. Actual prediction accuracy cannot be measured without ground-truth labels.</i></p>
  </div>
  <table>
    <thead><tr><th>Feature</th><th>KS Statistic</th><th>p-value</th><th>Status</th></tr></thead>
    <tbody>{''.join(html_rows)}</tbody>
  </table>
</body>
</html>"""
        html_path.write_text(html_content, encoding="utf-8")
        LOGGER.info("KS test drift HTML report generated: %s", html_path)

    summary["alert"] = bool(summary["drift_share"] >= threshold)

    # Persist per-run JSON
    json_path = report_dir / f"drift_summary_{run_id}.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # Append to rolling JSONL log with provenance
    rolling = report_dir / "drift_log.jsonl"
    with rolling.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "timestamp": summary["timestamp"],
            "data_source": source_label,
            "is_synthetic": is_synthetic,
            "drift_share": summary["drift_share"],
            "drifted_features": summary["drifted_feature_count"],
            "alert": summary["alert"],
        }) + "\n")

    level = logging.WARNING if summary["alert"] else logging.INFO
    LOGGER.log(
        level,
        "Drift check complete (source=%s) — share=%.0f%% | drifted=%d/%d | alert=%s",
        source_label,
        summary["drift_share"] * 100,
        summary["drifted_feature_count"],
        len(common_cols),
        summary["alert"],
    )
    return summary


def get_latest_drift_summary(report_dir: str | Path = "logs/drift") -> dict[str, Any] | None:
    """Return the most recent drift summary JSON, or None if no runs yet."""
    summaries = sorted(Path(report_dir).glob("drift_summary_*.json"))
    if not summaries:
        return None
    return json.loads(summaries[-1].read_text(encoding="utf-8"))


def get_drift_history(report_dir: str | Path = "logs/drift", last_n: int = 30) -> list[dict]:
    """Return the last N entries from the rolling drift log."""
    log_path = Path(report_dir) / "drift_log.jsonl"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-last_n:] if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgriAdapt drift detection")
    parser.add_argument("--reference", default="data/raw/Crop_recommendation.csv", help="Path to reference CSV")
    parser.add_argument("--prediction-log", default="logs/prediction_log.jsonl", help="Path to prediction log JSONL")
    parser.add_argument("--report-dir", default="logs/drift", help="Directory for drift reports")
    parser.add_argument("--run-id", default=None, help="Optional run ID")
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD, help="Alert threshold share [0.0, 1.0]")
    parser.add_argument("--synthetic", action="store_true", help="Explicitly use synthetic drift batch for demo or test")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    ref_df = load_reference_data(args.reference)
    cur_df = load_prediction_log(args.prediction_log, allow_synthetic=args.synthetic)
    drift_res = run_drift_detection(
        ref_df,
        cur_df,
        report_dir=args.report_dir,
        run_id=args.run_id,
        threshold=args.threshold,
    )
    print(json.dumps({k: v for k, v in drift_res.items() if k != "feature_drift"}, indent=2))
