"""Utilities for generating VAT payable by jurisdiction."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

SALE_TYPES = {"sale", "sales", "output", "invoice"}
PURCHASE_TYPES = {"purchase", "expense", "input", "bill"}
DIRECT_TYPES = {"adjustment", "direct"}
TWO_DP = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert input values safely to Decimal for currency math."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - exact exception varies by input
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


def _transaction_vat_effect(transaction: Mapping[str, Any]) -> Decimal:
    """
    Return the VAT effect for one transaction.

    Supported formats:
    1) Explicit netting fields:
       - vat_collected
       - vat_paid
       Net effect = vat_collected - vat_paid

    2) Type-based amount:
       - vat_amount
       - transaction_type (optional)
       Rules:
         * sale/output/invoice => +vat_amount
         * purchase/input/expense/bill => -vat_amount
         * adjustment/direct or missing type => signed vat_amount as-is
    """
    if "vat_collected" in transaction or "vat_paid" in transaction:
        collected = _to_decimal(transaction.get("vat_collected", 0), "vat_collected")
        paid = _to_decimal(transaction.get("vat_paid", 0), "vat_paid")
        return collected - paid

    if "vat_amount" not in transaction:
        raise ValueError("Transaction must include either vat_amount or vat_collected/vat_paid.")

    vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
    transaction_type = transaction.get("transaction_type")

    if transaction_type is None:
        return vat_amount

    normalized_type = str(transaction_type).strip().lower()
    if normalized_type in SALE_TYPES:
        return vat_amount
    if normalized_type in PURCHASE_TYPES:
        return -vat_amount
    if normalized_type in DIRECT_TYPES:
        return vat_amount

    raise ValueError(f"Unsupported transaction_type: {transaction_type!r}")


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Aggregate VAT payable for each jurisdiction."""
    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for transaction in transactions:
        raw_jurisdiction = transaction.get("jurisdiction")
        if raw_jurisdiction is None:
            raise ValueError("Each transaction must include 'jurisdiction'.")

        jurisdiction = str(raw_jurisdiction).strip()
        if not jurisdiction:
            raise ValueError("Jurisdiction cannot be blank.")

        totals[jurisdiction] += _transaction_vat_effect(transaction)

    return {
        jurisdiction: _quantize_currency(total)
        for jurisdiction, total in sorted(totals.items())
    }


def _serialize_for_json(totals: Mapping[str, Decimal]) -> dict[str, str]:
    return {jurisdiction: format(amount, ".2f") for jurisdiction, amount in totals.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amounts for each jurisdiction from JSON records."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a JSON file containing an array of transactions.",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as handle:
        transactions = json.load(handle)

    if not isinstance(transactions, list):
        raise ValueError("Input JSON must be an array of transaction objects.")

    totals = calculate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(_serialize_for_json(totals), indent=2))


if __name__ == "__main__":
    main()
