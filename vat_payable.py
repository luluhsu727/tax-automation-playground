#!/usr/bin/env python3
"""Generate VAT payable totals by jurisdiction from a transactions CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")

VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}

JURISDICTION_COLUMNS = ("jurisdiction", "country")
REVENUE_COLUMNS = ("revenue", "taxable_amount", "net_amount", "amount")
VAT_COLLECTED_COLUMNS = ("vat_collected", "collected_vat")
VAT_RATE_COLUMNS = ("vat_rate", "rate")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid decimal value for '{field_name}': {raw_value}") from exc


def _resolve_column(
    fieldnames: Iterable[str],
    candidates: tuple[str, ...],
    *,
    required: bool,
) -> str | None:
    lookup = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    if required:
        raise ValueError(f"Missing required column. Expected one of: {', '.join(candidates)}")
    return None


def _normalize_transactions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")

        jurisdiction_col = _resolve_column(
            reader.fieldnames, JURISDICTION_COLUMNS, required=True
        )
        revenue_col = _resolve_column(reader.fieldnames, REVENUE_COLUMNS, required=True)
        vat_collected_col = _resolve_column(
            reader.fieldnames, VAT_COLLECTED_COLUMNS, required=True
        )
        vat_rate_col = _resolve_column(reader.fieldnames, VAT_RATE_COLUMNS, required=False)

        transactions: list[dict[str, Any]] = []
        for idx, row in enumerate(reader, start=2):
            jurisdiction = str(row.get(jurisdiction_col, "")).strip().upper()
            if not jurisdiction:
                raise ValueError(f"Missing jurisdiction value on row {idx}.")

            revenue = _parse_decimal(row.get(revenue_col, ""), revenue_col)
            collected = _parse_decimal(row.get(vat_collected_col, ""), vat_collected_col)

            vat_rate: Decimal | None = None
            if vat_rate_col:
                raw_rate = str(row.get(vat_rate_col, "")).strip()
                if raw_rate:
                    vat_rate = _parse_decimal(raw_rate, vat_rate_col)

            transactions.append(
                {
                    "jurisdiction": jurisdiction,
                    "revenue": revenue,
                    "vat_collected": collected,
                    "vat_rate": vat_rate,
                }
            )

    return transactions


def generate_vat_payable_by_jurisdiction(input_path: Path, output_path: Path) -> None:
    """Read transaction CSV and write VAT payable totals grouped by jurisdiction."""
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "total_revenue": Decimal("0.00"),
            "total_vat_collected": Decimal("0.00"),
            "total_expected_vat": Decimal("0.00"),
        }
    )

    transactions = _normalize_transactions(input_path)
    for row in transactions:
        jurisdiction = str(row["jurisdiction"]).upper()
        vat_rate = row["vat_rate"] if row["vat_rate"] is not None else VAT_RATES.get(jurisdiction)
        if vat_rate is None:
            raise ValueError(f"Unsupported jurisdiction code: {jurisdiction}")

        revenue = _parse_decimal(row["revenue"], "revenue")
        vat_collected = _parse_decimal(row["vat_collected"], "vat_collected")
        expected_vat = _money(revenue * vat_rate)

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
            vat_to_be_paid = _money(
                jurisdiction_totals["total_expected_vat"]
                - jurisdiction_totals["total_vat_collected"]
            )
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "total_revenue": f"{_money(jurisdiction_totals['total_revenue']):.2f}",
                    "total_vat_collected": f"{_money(jurisdiction_totals['total_vat_collected']):.2f}",
                    "total_expected_vat": f"{_money(jurisdiction_totals['total_expected_vat']):.2f}",
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
