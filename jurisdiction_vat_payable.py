#!/usr/bin/env python3
"""Generate VAT payable totals grouped by jurisdiction."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")

DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}

JURISDICTION_COLUMNS = ("jurisdiction", "country")
TAXABLE_AMOUNT_COLUMNS = ("taxable_amount", "net_amount", "revenue", "amount")
VAT_RATE_COLUMNS = ("vat_rate", "rate")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for '{field_name}': {raw_value}") from exc


def _resolve_column(fieldnames: Iterable[str], candidates: tuple[str, ...]) -> str:
    lookup = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    raise ValueError(f"Missing required column. Expected one of: {', '.join(candidates)}")


def load_transactions(path: Path) -> list[dict[str, Decimal | str | None]]:
    """Load transaction rows from CSV and normalize key fields."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")

        jurisdiction_col = _resolve_column(reader.fieldnames, JURISDICTION_COLUMNS)
        taxable_col = _resolve_column(reader.fieldnames, TAXABLE_AMOUNT_COLUMNS)
        try:
            vat_rate_col = _resolve_column(reader.fieldnames, VAT_RATE_COLUMNS)
        except ValueError:
            vat_rate_col = None

        transactions: list[dict[str, Decimal | str | None]] = []
        for idx, row in enumerate(reader, start=2):
            jurisdiction = str(row.get(jurisdiction_col, "")).strip().upper()
            if not jurisdiction:
                raise ValueError(f"Missing jurisdiction value on row {idx}.")

            taxable_amount = _parse_decimal(row.get(taxable_col, ""), taxable_col)
            vat_rate: Decimal | None = None
            if vat_rate_col:
                raw_rate = str(row.get(vat_rate_col, "")).strip()
                if raw_rate:
                    vat_rate = _parse_decimal(raw_rate, vat_rate_col)

            transactions.append(
                {
                    "jurisdiction": jurisdiction,
                    "taxable_amount": taxable_amount,
                    "vat_rate": vat_rate,
                }
            )

    return transactions


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Aggregate VAT payable totals by jurisdiction."""
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"total_taxable_amount": Decimal("0.00"), "total_vat_payable": Decimal("0.00")}
    )

    for row in transactions:
        jurisdiction = str(row.get("jurisdiction", "")).strip().upper()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction.")

        taxable_amount = _parse_decimal(row.get("taxable_amount"), "taxable_amount")
        vat_rate_value = row.get("vat_rate")
        vat_rate = _parse_decimal(vat_rate_value, "vat_rate") if vat_rate_value is not None else None

        if vat_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(
                    f"No VAT rate supplied for jurisdiction '{jurisdiction}', "
                    "and no default rate is configured."
                )
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]

        vat_payable = _money(taxable_amount * vat_rate)
        totals[jurisdiction]["total_taxable_amount"] += taxable_amount
        totals[jurisdiction]["total_vat_payable"] += vat_payable

    summary_rows: list[dict[str, str]] = []
    for jurisdiction in sorted(totals):
        taxable_total = _money(totals[jurisdiction]["total_taxable_amount"])
        payable_total = _money(totals[jurisdiction]["total_vat_payable"])
        effective_rate = (
            _money(payable_total / taxable_total) if taxable_total != Decimal("0.00") else Decimal("0.00")
        )
        summary_rows.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{payable_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )

    return summary_rows


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Return only VAT-to-be-paid amount for each jurisdiction."""
    summary = compute_vat_payable_by_jurisdiction(transactions)
    return {row["jurisdiction"]: Decimal(row["total_vat_payable"]) for row in summary}


def write_summary(path: Path, summary_rows: list[dict[str, str]]) -> None:
    """Write jurisdiction-level VAT payable summary CSV."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        default="sample_transactions.csv",
        help="Input transactions CSV path.",
    )
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Output CSV path for jurisdiction summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transactions = load_transactions(Path(args.input))
    summary_rows = compute_vat_payable_by_jurisdiction(transactions)
    write_summary(Path(args.output), summary_rows)
    print(f"Wrote {len(summary_rows)} jurisdiction rows to {args.output}")


if __name__ == "__main__":
    main()
