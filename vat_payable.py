#!/usr/bin/env python3
"""Generate VAT payable totals by jurisdiction from a transactions CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


VAT_RATES = {
    "DE": 0.19,
    "FR": 0.20,
    "ES": 0.21,
    "IT": 0.22,
}


def _jurisdiction_column(fieldnames: list[str]) -> str:
    if "jurisdiction" in fieldnames:
        return "jurisdiction"
    if "country" in fieldnames:
        return "country"
    raise ValueError("Input CSV must include either 'jurisdiction' or 'country' column.")


def generate_vat_payable_by_jurisdiction(input_path: Path, output_path: Path) -> None:
    """Read transaction CSV and write VAT payable totals grouped by jurisdiction."""
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "total_revenue": 0.0,
            "total_vat_collected": 0.0,
            "total_expected_vat": 0.0,
        }
    )

    with input_path.open("r", newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = list(reader.fieldnames or [])
        jurisdiction_column = _jurisdiction_column(fieldnames)

        required_columns = {"transaction_id", "revenue", "vat_collected", jurisdiction_column}
        missing_columns = sorted(required_columns - set(fieldnames))
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        for row in reader:
            jurisdiction = (row.get(jurisdiction_column) or "").strip().upper()
            vat_rate = VAT_RATES.get(jurisdiction)
            if vat_rate is None:
                raise ValueError(f"Unsupported jurisdiction code: {jurisdiction}")

            revenue = float(row["revenue"])
            vat_collected = float(row["vat_collected"])
            expected_vat = revenue * vat_rate

            totals[jurisdiction]["total_revenue"] += revenue
            totals[jurisdiction]["total_vat_collected"] += vat_collected
            totals[jurisdiction]["total_expected_vat"] += expected_vat

    output_fields = [
        "jurisdiction",
        "total_revenue",
        "total_vat_collected",
        "total_expected_vat",
        "vat_to_be_paid",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_fields)
        writer.writeheader()
        for jurisdiction in sorted(totals):
            jurisdiction_totals = totals[jurisdiction]
            vat_to_be_paid = (
                jurisdiction_totals["total_expected_vat"]
                - jurisdiction_totals["total_vat_collected"]
            )
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "total_revenue": f"{jurisdiction_totals['total_revenue']:.2f}",
                    "total_vat_collected": f"{jurisdiction_totals['total_vat_collected']:.2f}",
                    "total_expected_vat": f"{jurisdiction_totals['total_expected_vat']:.2f}",
                    "vat_to_be_paid": f"{vat_to_be_paid:.2f}",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("--input", required=True, help="Path to input transactions CSV")
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Path to output CSV containing VAT payable by jurisdiction",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_vat_payable_by_jurisdiction(Path(args.input), Path(args.output))
    print(f"Wrote VAT payable-by-jurisdiction report: {args.output}")


if __name__ == "__main__":
    main()
