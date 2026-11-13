"""
run_data_ingestion.py
─────────────────────
Command-line runner for the AgriAdapt AI Real-World Data Ingestion Pipeline.
Acquires real-world meteorological, soil moisture, and surveillance records for Maharashtra.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.data_ingestion.data_alignment import run_data_alignment_pipeline
from src.data_ingestion.pest_surveillance_ingestion import (
    check_surveillance_data_availability,
    create_surveillance_template,
)
from src.data_ingestion.weather_ingestion import MAHARASHTRA_DISTRICT_COORDINATES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
LOGGER = logging.getLogger("run_data_ingestion")


def main() -> int:
    parser = argparse.ArgumentParser(description="AgriAdapt AI Data Ingestion & Alignment Runner")
    parser.add_argument(
        "--districts",
        nargs="+",
        default=["Nagpur", "Amravati", "Yavatmal", "Jalgaon"],
        help="List of Maharashtra districts to ingest",
    )
    parser.add_argument(
        "--start-date",
        default="2023-06-01",
        help="Start date in YYYY-MM-DD format (default: 2023-06-01)",
    )
    parser.add_argument(
        "--end-date",
        default="2023-10-31",
        help="End date in YYYY-MM-DD format (default: 2023-10-31)",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass local raw cache and fetch freshly from APIs",
    )
    parser.add_argument(
        "--create-surveillance-template",
        action="store_true",
        help="Generate a standardized surveillance CSV template for data partners",
    )

    args = parser.parse_args()

    LOGGER.info("=" * 70)
    LOGGER.info("AGRIADAPT AI — REAL-WORLD DATA ACQUISITION & INGESTION")
    LOGGER.info("=" * 70)

    # 1. Create template if requested
    if args.create_surveillance_template:
        t_path = create_surveillance_template()
        LOGGER.info("Surveillance template ready at: %s", t_path)

    # 2. Check surveillance availability
    surv_audit = check_surveillance_data_availability()
    LOGGER.info("Pest Surveillance Status: %s", surv_audit.status)
    if surv_audit.status != "AVAILABLE":
        LOGGER.info("Note: %s", surv_audit.notes)

    # 3. Run Ingestion and Alignment
    try:
        df_aligned, report = run_data_alignment_pipeline(
            districts=args.districts,
            start_date=args.start_date,
            end_date=args.end_date,
            force_refresh=args.force_refresh,
        )

        LOGGER.info("-" * 70)
        LOGGER.info("INGESTION & ALIGNMENT SUMMARY:")
        LOGGER.info("  Total Aligned Records: %d", report.total_aligned_records)
        LOGGER.info("  Districts Processed: %s", ", ".join(report.districts))
        LOGGER.info("  Temporal Span: %s to %s", report.date_span[0], report.date_span[1])
        LOGGER.info("  Surveillance Matched Records: %d", report.surveillance_matched_records)
        LOGGER.info("  Alignment Status: %s", report.alignment_status)
        LOGGER.info("  Output CSV: %s", report.output_filepath)
        LOGGER.info("-" * 70)

        # Print snapshot of aligned columns
        LOGGER.info("Columns in Aligned Dataset (%d columns):", len(df_aligned.columns))
        LOGGER.info("  %s", ", ".join(df_aligned.columns))
        LOGGER.info("Sample Record (Observation #0):")
        LOGGER.info("  Date: %s, District: %s, T_mean: %.1f°C, RH: %.1f%%, Rain: %.1fmm, Rain7d: %.1fmm, SM: %.1f%%",
                    df_aligned.iloc[0]["observation_date"].strftime("%Y-%m-%d"),
                    df_aligned.iloc[0]["district"],
                    df_aligned.iloc[0]["temperature_mean"],
                    df_aligned.iloc[0]["humidity_mean"],
                    df_aligned.iloc[0]["rainfall_mm"],
                    df_aligned.iloc[0]["rainfall_7d"],
                    df_aligned.iloc[0]["soil_moisture_pct"])
        LOGGER.info("=" * 70)
        return 0

    except Exception as exc:
        LOGGER.exception("Fatal error during data ingestion pipeline: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

