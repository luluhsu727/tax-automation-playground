#!/usr/bin/env python3
"""Compute VAT payable per jurisdiction from transaction data."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


MONEY_QUANT = Decimal("0.01")
ZERO = Decimal("0.00")

OUTPUT_VAT_COLUMNS = ("vat_collected", "output_vat", "sales_vat", "vat_output")
INPUT_VAT_COLUMNS = ("vat_deductible", "input_vat", "purchase_vat", "vat_input")
VAT_AMOUNT_COLUMNS = ("vat_amount",)
VAT_TYPE_COLUMNS = ("vat_type", "transaction_type", "type")
JURISDICTION_COLUMNS = ("jurisdiction", "country", "region")
TAXABLE_AMOUNT_COLUMNS = ("taxable_amount", "net_amount", "amount_ex_vat", "amount")
VAT_RATE_COLUMNS = ("vat_rate", "tax_rate", "rate")

OUTPUT_TYPES = {"output", "collected", "sales", "sale", "payable"}
INPUT_TYPES = {"input", "deductible", "purchase", "refund", "credit"}


@dataclass(frozen=True)
class TransactionVAT:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal


def quantize_money(value: Decimal) -> Decimal:
    """Round values to two decimal places using standard half-up rounding."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def parse_decimal(value: str, field_name: str) -> Decimal:
    """Parse a decimal value from a CSV field."""
    cleaned = (value or "").strip()
    if not cleaned:
        return ZERO
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def first_present(row: dict[str, str], column_names: Iterable[str]) -> str | None:
    """Return the first present column value from a row."""
    for name in column_names:
        if name in row and row[name] is not None:
            return row[name]
    return None


def first_existing_key(row: dict[str, str], column_names: Iterable[str]) -> str | None:
    """Return the first existing key from a row."""
    for name in column_names:
        if name in row:
            return name
    return None


def normalize_vat_rate(raw_rate: Decimal) -> Decimal:
    """Normalize VAT rates; allows 20 and 0.20 forms."""
    if raw_rate > 1:
        return raw_rate / Decimal("100")
    return raw_rate


def row_to_transaction(row: dict[str, str]) -> TransactionVAT:
    """Convert a CSV row to normalized VAT components."""
    jurisdiction = (first_present(row, JURISDICTION_COLUMNS) or "").strip()
    if not jurisdiction:
        raise ValueError("Missing required jurisdiction value.")

    output_vat = ZERO
    input_vat = ZERO
    has_explicit_vat = False

    for column in OUTPUT_VAT_COLUMNS:
        if column in row:
            output_vat += parse_decimal(row.get(column, ""), column)
            has_explicit_vat = True

    for column in INPUT_VAT_COLUMNS:
        if column in row:
            input_vat += parse_decimal(row.get(column, ""), column)
            has_explicit_vat = True

    vat_amount_key = first_existing_key(row, VAT_AMOUNT_COLUMNS)
    vat_type_raw = first_present(row, VAT_TYPE_COLUMNS)
    if vat_amount_key is not None:
        vat_amount = parse_decimal(row.get(vat_amount_key, ""), vat_amount_key)
        if vat_type_raw is None:
            raise ValueError(
                f"Row for jurisdiction '{jurisdiction}' includes '{vat_amount_key}' "
                "but no VAT type (expected vat_type / transaction_type / type)."
            )
        vat_type = vat_type_raw.strip().lower()
        if vat_type in OUTPUT_TYPES:
            output_vat += vat_amount
        elif vat_type in INPUT_TYPES:
            input_vat += vat_amount
        else:
            raise ValueError(
                f"Unsupported VAT type '{vat_type_raw}' for jurisdiction '{jurisdiction}'."
            )
        has_explicit_vat = True

    if not has_explicit_vat:
        taxable_key = first_existing_key(row, TAXABLE_AMOUNT_COLUMNS)
        rate_key = first_existing_key(row, VAT_RATE_COLUMNS)
        if taxable_key and rate_key:
            if vat_type_raw is None:
                raise ValueError(
                    f"Row for jurisdiction '{jurisdiction}' includes taxable amount/rate "
                    "but no VAT type (expected output/input style type)."
                )
            taxable = parse_decimal(row.get(taxable_key, ""), taxable_key)
            rate = normalize_vat_rate(parse_decimal(row.get(rate_key, ""), rate_key))
            vat_amount = taxable * rate
            vat_type = vat_type_raw.strip().lower()
            if vat_type in OUTPUT_TYPES:
                output_vat += vat_amount
            elif vat_type in INPUT_TYPES:
                input_vat += vat_amount
            else:
                raise ValueError(
                    f"Unsupported VAT type '{vat_type_raw}' for jurisdiction '{jurisdiction}'."
                )
        else:
            raise ValueError(
                f"Row for jurisdiction '{jurisdiction}' does not include usable VAT fields."
            )

    return TransactionVAT(
        jurisdiction=jurisdiction,
        output_vat=quantize_money(output_vat),
        input_vat=quantize_money(input_vat),
    )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[TransactionVAT],
) -> list[dict[str, str]]:
    """Aggregate VAT and compute payable amount by jurisdiction."""
    aggregates: dict[str, dict[str, Decimal]] = {}
    for tx in transactions:
        if tx.jurisdiction not in aggregates:
            aggregates[tx.jurisdiction] = {"output_vat": ZERO, "input_vat": ZERO}
        aggregates[tx.jurisdiction]["output_vat"] += tx.output_vat
        aggregates[tx.jurisdiction]["input_vat"] += tx.input_vat

    results: list[dict[str, str]] = []
    for jurisdiction in sorted(aggregates):
        output_vat = quantize_money(aggregates[jurisdiction]["output_vat"])
        input_vat = quantize_money(aggregates[jurisdiction]["input_vat"])
        net_vat = quantize_money(output_vat - input_vat)
        vat_to_be_paid = quantize_money(net_vat if net_vat > ZERO else ZERO)
        vat_credit_carry_forward = quantize_money(-net_vat if net_vat < ZERO else ZERO)
        results.append(
            {
                "jurisdiction": jurisdiction,
                "output_vat": f"{output_vat:.2f}",
                "input_vat": f"{input_vat:.2f}",
                "net_vat": f"{net_vat:.2f}",
                "vat_to_be_paid": f"{vat_to_be_paid:.2f}",
                "vat_credit_carry_forward": f"{vat_credit_carry_forward:.2f}",
            }
        )
    return results


def read_transactions_from_csv(csv_path: Path) -> list[TransactionVAT]:
    """Read and normalize transaction rows from CSV."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV input must include headers.")
        return [row_to_transaction(row) for row in reader]


def write_results(rows: Iterable[dict[str, str]], output_path: Path) -> None:
    """Write VAT payable rows to CSV."""
    fieldnames = [
        "jurisdiction",
        "output_vat",
        "input_vat",
        "net_vat",
        "vat_to_be_paid",
        "vat_credit_carry_forward",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction from a CSV file."
    )
    parser.add_argument("input_csv", type=Path, help="Path to input CSV transactions file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("vat_payable_by_jurisdiction.csv"),
        help="Output CSV path (default: vat_payable_by_jurisdiction.csv).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    transactions = read_transactions_from_csv(args.input_csv)
    results = calculate_vat_payable_by_jurisdiction(transactions)
    write_results(results, args.output)
    print(f"Wrote {len(results)} jurisdiction rows to {args.output}")


if __name__ == "__main__":
    main()
