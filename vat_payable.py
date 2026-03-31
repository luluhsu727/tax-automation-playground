#!/usr/bin/env python3
"""Generate VAT payable totals for each jurisdiction from a CSV file."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

TWOPLACES = Decimal("0.01")

OUTPUT_TYPES = {"sale", "sales", "output", "out"}
INPUT_TYPES = {"purchase", "purchases", "input", "in"}


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    direction: int
    vat_amount: Decimal


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def parse_decimal(raw: str | None, field_name: str) -> Decimal:
    if raw is None:
        raise ValueError(f"Missing required field: {field_name}")
    text = raw.strip()
    if not text:
        raise ValueError(f"Empty value for required field: {field_name}")
    try:
        return Decimal(text)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid decimal value for {field_name}: {raw}") from exc


def parse_direction(raw: str) -> int:
    text = raw.strip().lower()
    if text in OUTPUT_TYPES:
        return 1
    if text in INPUT_TYPES:
        return -1
    raise ValueError(
        "Invalid transaction_type. Expected one of "
        f"{sorted(OUTPUT_TYPES | INPUT_TYPES)}, got: {raw}"
    )


def build_transaction(row: dict[str, str]) -> Transaction:
    jurisdiction = row.get("jurisdiction", "").strip()
    if not jurisdiction:
        raise ValueError("Missing required field: jurisdiction")

    tx_type = row.get("transaction_type", "")
    if not tx_type.strip():
        raise ValueError("Missing required field: transaction_type")
    direction = parse_direction(tx_type)

    vat_amount_raw = (row.get("vat_amount") or "").strip()
    if vat_amount_raw:
        vat_amount = parse_decimal(vat_amount_raw, "vat_amount")
    else:
        net_amount = parse_decimal(row.get("net_amount"), "net_amount")
        vat_rate = parse_decimal(row.get("vat_rate"), "vat_rate")
        vat_amount = net_amount * vat_rate

    return Transaction(
        jurisdiction=jurisdiction,
        direction=direction,
        vat_amount=quantize_money(vat_amount),
    )


def load_transactions_from_csv(path: Path) -> list[Transaction]:
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_headers = {"jurisdiction", "transaction_type"}
        missing_headers = required_headers - set(reader.fieldnames or [])
        if missing_headers:
            missing = ", ".join(sorted(missing_headers))
            raise ValueError(f"CSV missing required column(s): {missing}")

        transactions: list[Transaction] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                transactions.append(build_transaction(row))
            except ValueError as exc:
                raise ValueError(f"Row {line_number}: {exc}") from exc
        return transactions


def aggregate_vat_payable(transactions: Iterable[Transaction]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for tx in transactions:
        totals[tx.jurisdiction] += tx.vat_amount * tx.direction

    return {
        jurisdiction: quantize_money(amount)
        for jurisdiction, amount in sorted(totals.items())
    }


def to_json_ready(totals: dict[str, Decimal]) -> dict[str, str]:
    return {jurisdiction: format(amount, ".2f") for jurisdiction, amount in totals.items()}


def print_table(totals: dict[str, Decimal]) -> None:
    if not totals:
        print("No transactions found.")
        return

    header_left = "Jurisdiction"
    header_right = "VAT Payable"
    left_width = max(len(header_left), *(len(k) for k in totals.keys()))
    right_width = max(len(header_right), *(len(format(v, ".2f")) for v in totals.values()))

    print(f"{header_left:<{left_width}}  {header_right:>{right_width}}")
    print(f"{'-' * left_width}  {'-' * right_width}")
    for jurisdiction, amount in totals.items():
        print(f"{jurisdiction:<{left_width}}  {format(amount, '.2f'):>{right_width}}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input CSV with VAT transactions.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for VAT totals.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transactions = load_transactions_from_csv(args.input)
    totals = aggregate_vat_payable(transactions)

    if args.format == "json":
        print(json.dumps(to_json_ready(totals), indent=2, sort_keys=True))
    else:
        print_table(totals)


if __name__ == "__main__":
    main()
