#!/usr/bin/env python3
"""Generate VAT payable totals grouped by jurisdiction."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

DEFAULT_VAT_RATES: Dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}

JURISDICTION_COLUMNS = ("jurisdiction", "country")
TAXABLE_AMOUNT_COLUMNS = ("taxable_amount", "net_amount", "revenue", "amount")
VAT_RATE_COLUMNS = ("vat_rate", "rate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction data."
    )
    parser.add_argument(
        "--input",
        default="sample_transactions.csv",
        help="Input transactions CSV file path.",
    )
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Output CSV file path for jurisdiction VAT totals.",
    )
    return parser.parse_args()


def quantize_two_decimals(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def resolve_column(fieldnames: Iterable[str], candidates: Tuple[str, ...]) -> str:
    fieldname_lookup = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in fieldname_lookup:
            return fieldname_lookup[candidate]
    raise ValueError(f"Missing required column. Expected one of: {', '.join(candidates)}")


def parse_decimal(raw_value: str, column_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - normalized error path
        raise ValueError(f"Invalid numeric value '{raw_value}' in column '{column_name}'") from exc


def load_transactions(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")

        jurisdiction_col = resolve_column(reader.fieldnames, JURISDICTION_COLUMNS)
        taxable_col = resolve_column(reader.fieldnames, TAXABLE_AMOUNT_COLUMNS)
        vat_rate_col = None
        try:
            vat_rate_col = resolve_column(reader.fieldnames, VAT_RATE_COLUMNS)
        except ValueError:
            vat_rate_col = None

        transactions = []
        for index, row in enumerate(reader, start=2):
            jurisdiction = str(row.get(jurisdiction_col, "")).strip().upper()
            if not jurisdiction:
                raise ValueError(f"Missing jurisdiction value on row {index}.")

            taxable_amount = parse_decimal(str(row.get(taxable_col, "")), taxable_col)

            if vat_rate_col:
                rate_raw = str(row.get(vat_rate_col, "")).strip()
                vat_rate = parse_decimal(rate_raw, vat_rate_col) if rate_raw else None
            else:
                vat_rate = None

            transactions.append(
                {
                    "jurisdiction": jurisdiction,
                    "taxable_amount": taxable_amount,
                    "vat_rate": vat_rate,
                }
            )
        return transactions


def compute_vat_payable_by_jurisdiction(transactions: List[dict]) -> List[dict]:
    totals = defaultdict(lambda: {"taxable_amount": Decimal("0"), "vat_payable": Decimal("0")})

    for row in transactions:
        jurisdiction = row["jurisdiction"]
        taxable_amount = row["taxable_amount"]
        vat_rate = row["vat_rate"]

        if vat_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(
                    f"No VAT rate supplied for jurisdiction '{jurisdiction}', "
                    "and no default rate is configured."
                )
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]

        vat_payable = quantize_two_decimals(taxable_amount * vat_rate)

        totals[jurisdiction]["taxable_amount"] += taxable_amount
        totals[jurisdiction]["vat_payable"] += vat_payable

    summary_rows: List[dict] = []
    for jurisdiction in sorted(totals):
        taxable_total = quantize_two_decimals(totals[jurisdiction]["taxable_amount"])
        vat_total = quantize_two_decimals(totals[jurisdiction]["vat_payable"])
        effective_rate = (
            quantize_two_decimals(vat_total / taxable_total)
            if taxable_total != Decimal("0")
            else Decimal("0.00")
        )
        summary_rows.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{vat_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )

    return summary_rows


def write_summary(path: Path, summary_rows: List[dict]) -> None:
    fieldnames = (
        "jurisdiction",
        "total_taxable_amount",
        "total_vat_payable",
        "effective_vat_rate",
    )
    with path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    transactions = load_transactions(input_path)
    summary_rows = compute_vat_payable_by_jurisdiction(transactions)
    write_summary(output_path, summary_rows)

    print(f"Wrote {len(summary_rows)} jurisdiction rows to {output_path}")


if __name__ == "__main__":
    main()
