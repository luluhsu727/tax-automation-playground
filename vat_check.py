#!/usr/bin/env python3
"""Generate VAT reconciliation outputs, including VAT payable by jurisdiction."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


MONEY_PLACES = Decimal("0.01")
VAT_RATES = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(raw: str, field_name: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {raw!r}") from exc


def _get_jurisdiction_column(fieldnames: list[str]) -> str:
    if "jurisdiction" in fieldnames:
        return "jurisdiction"
    if "country" in fieldnames:
        return "country"
    raise ValueError("Input CSV must include either 'jurisdiction' or 'country' column.")


def process_transactions(
    input_path: Path, output_path: Path, summary_output_path: Path
) -> None:
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        jurisdiction_column = _get_jurisdiction_column(fieldnames)

        required = {"transaction_id", "revenue", "vat_collected", jurisdiction_column}
        missing = required - set(fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        output_fields = fieldnames + ["vat_rate", "expected_vat", "vat_payable"]
        processed_rows: list[dict[str, str]] = []
        summary_totals: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {
                "total_revenue": Decimal("0"),
                "total_vat_collected": Decimal("0"),
                "total_expected_vat": Decimal("0"),
            }
        )

        for row in reader:
            jurisdiction = (row.get(jurisdiction_column) or "").strip().upper()
            vat_rate = VAT_RATES.get(jurisdiction)
            if vat_rate is None:
                raise ValueError(f"Unsupported jurisdiction code: {jurisdiction}")

            revenue = _parse_decimal(row["revenue"], "revenue")
            vat_collected = _parse_decimal(row["vat_collected"], "vat_collected")
            expected_vat = _to_money(revenue * vat_rate)
            vat_payable = _to_money(expected_vat - vat_collected)

            row.update(
                {
                    jurisdiction_column: jurisdiction,
                    "revenue": f"{_to_money(revenue):.2f}",
                    "vat_collected": f"{_to_money(vat_collected):.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "expected_vat": f"{expected_vat:.2f}",
                    "vat_payable": f"{vat_payable:.2f}",
                }
            )
            processed_rows.append(row)

            summary_totals[jurisdiction]["total_revenue"] += revenue
            summary_totals[jurisdiction]["total_vat_collected"] += vat_collected
            summary_totals[jurisdiction]["total_expected_vat"] += expected_vat

    processed_rows.sort(key=lambda r: abs(Decimal(r["vat_payable"])), reverse=True)
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(processed_rows)

    summary_fields = [
        "jurisdiction",
        "total_revenue",
        "total_vat_collected",
        "total_expected_vat",
        "vat_payable",
    ]
    with summary_output_path.open("w", newline="", encoding="utf-8") as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=summary_fields)
        writer.writeheader()
        for jurisdiction in sorted(summary_totals):
            totals = summary_totals[jurisdiction]
            vat_payable = _to_money(
                totals["total_expected_vat"] - totals["total_vat_collected"]
            )
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "total_revenue": f"{_to_money(totals['total_revenue']):.2f}",
                    "total_vat_collected": f"{_to_money(totals['total_vat_collected']):.2f}",
                    "total_expected_vat": f"{_to_money(totals['total_expected_vat']):.2f}",
                    "vat_payable": f"{vat_payable:.2f}",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable output for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        default="/home/ubuntu/.cursor/projects/workspace/uploads/practice_dataset_-_Sheet1.csv",
        help="Path to source transactions CSV.",
    )
    parser.add_argument(
        "--output",
        default="vat_check_results.csv",
        help="Path to output CSV with transaction-level VAT calculations.",
    )
    parser.add_argument(
        "--summary-output",
        default="vat_payable_by_jurisdiction.csv",
        help="Path to output CSV with VAT payable by jurisdiction.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_transactions(Path(args.input), Path(args.output), Path(args.summary_output))
    print(f"Wrote transaction-level VAT calculations to: {args.output}")
    print(f"Wrote VAT payable-by-jurisdiction summary to: {args.summary_output}")


if __name__ == "__main__":
    main()
