"""Generate VAT payable per jurisdiction from transaction data."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

TWOPLACES = Decimal("0.01")
OUTPUT_TYPES = {"sale", "sales", "output"}
INPUT_TYPES = {"purchase", "purchases", "expense", "input"}


def _to_decimal(value: Any, field_name: str, transaction_index: int) -> Decimal:
    if value is None or value == "":
        raise ValueError(
            f"Transaction {transaction_index}: missing required '{field_name}' value"
        )

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"Transaction {transaction_index}: invalid decimal for '{field_name}': {value!r}"
        ) from exc


def _normalize_transaction_type(transaction: dict[str, Any], transaction_index: int) -> str:
    tx_type = (
        str(transaction.get("transaction_type") or transaction.get("type") or "")
        .strip()
        .lower()
    )
    if tx_type in OUTPUT_TYPES:
        return "output"
    if tx_type in INPUT_TYPES:
        return "input"

    raise ValueError(
        f"Transaction {transaction_index}: unknown transaction_type/type '{tx_type}'"
    )


def _extract_vat_amount(transaction: dict[str, Any], transaction_index: int) -> Decimal:
    vat_amount_raw = transaction.get("vat_amount")
    if vat_amount_raw is not None and vat_amount_raw != "":
        return _to_decimal(vat_amount_raw, "vat_amount", transaction_index).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )

    amount = _to_decimal(transaction.get("amount"), "amount", transaction_index)
    rate = _to_decimal(transaction.get("vat_rate"), "vat_rate", transaction_index)
    if rate > Decimal("1"):
        rate = rate / Decimal("100")

    return (amount * rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, Decimal | str]]:
    """Aggregate VAT by jurisdiction and calculate net payable amount.

    Returns a dictionary keyed by jurisdiction with:
      - output_vat: VAT collected from sales
      - input_vat: VAT paid on purchases/expenses
      - vat_payable: output_vat - input_vat
      - status: "payable" if positive, "refundable" if negative, else "balanced"
    """

    totals = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for index, transaction in enumerate(transactions, start=1):
        jurisdiction = str(transaction.get("jurisdiction") or "").strip()
        if not jurisdiction:
            raise ValueError(f"Transaction {index}: missing required 'jurisdiction'")

        tx_type = _normalize_transaction_type(transaction, index)
        vat_amount = _extract_vat_amount(transaction, index)

        bucket = totals[jurisdiction]
        if tx_type == "output":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: dict[str, dict[str, Decimal | str]] = {}
    for jurisdiction in sorted(totals):
        output_vat = totals[jurisdiction]["output_vat"].quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        input_vat = totals[jurisdiction]["input_vat"].quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        payable = (output_vat - input_vat).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        if payable > 0:
            status = "payable"
        elif payable < 0:
            status = "refundable"
        else:
            status = "balanced"

        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": payable,
            "status": status,
        }

    return result


def load_transactions_from_csv(csv_path: str | Path) -> list[dict[str, str]]:
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_vat_summary_csv(
    summary: dict[str, dict[str, Decimal | str]], output_path: str | Path
) -> None:
    fieldnames = ["jurisdiction", "output_vat", "input_vat", "vat_payable", "status"]
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for jurisdiction in sorted(summary):
            row = summary[jurisdiction]
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "output_vat": row["output_vat"],
                    "input_vat": row["input_vat"],
                    "vat_payable": row["vat_payable"],
                    "status": row["status"],
                }
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction CSV data."
    )
    parser.add_argument("input_csv", help="Input CSV path.")
    parser.add_argument(
        "--output-csv",
        help="Optional output CSV path. If omitted, prints summary to stdout as CSV.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    transactions = load_transactions_from_csv(args.input_csv)
    summary = generate_vat_payable_by_jurisdiction(transactions)

    if args.output_csv:
        write_vat_summary_csv(summary, args.output_csv)
        return

    writer = csv.writer(sys.stdout)
    writer.writerow(["jurisdiction", "output_vat", "input_vat", "vat_payable", "status"])
    for jurisdiction in sorted(summary):
        row = summary[jurisdiction]
        writer.writerow(
            [
                jurisdiction,
                row["output_vat"],
                row["input_vat"],
                row["vat_payable"],
                row["status"],
            ]
        )


if __name__ == "__main__":
    main()
