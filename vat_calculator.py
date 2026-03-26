#!/usr/bin/env python3
"""Compute VAT payable per jurisdiction from transaction records."""

from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")
OUTPUT_TRANSACTION_TYPES = {"sale", "output"}
INPUT_TRANSACTION_TYPES = {"purchase", "input"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Parse numbers safely as Decimal."""
    if value is None:
        raise ValueError(f"Missing '{field_name}'")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Normalize VAT rate so both 0.2 and 20 are accepted."""
    if rate < 0:
        raise ValueError("VAT rate cannot be negative")
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _resolve_vat_amount(transaction: dict[str, Any]) -> Decimal:
    """Get VAT amount from explicit vat_amount or net_amount * vat_rate."""
    vat_amount = transaction.get("vat_amount")
    if vat_amount is not None:
        return _to_decimal(vat_amount, "vat_amount")

    net_amount = _to_decimal(transaction.get("net_amount"), "net_amount")
    vat_rate = _normalize_rate(_to_decimal(transaction.get("vat_rate"), "vat_rate"))
    return net_amount * vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Any]],
) -> dict[str, str]:
    """
    Calculate VAT payable per jurisdiction.

    VAT payable is computed as:
      output VAT (sales) - input VAT (purchases)
    """
    totals: dict[str, Decimal] = {}

    for idx, transaction in enumerate(transactions):
        if not isinstance(transaction, dict):
            raise ValueError(f"Transaction at index {idx} must be an object")

        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(f"Transaction at index {idx} missing valid 'jurisdiction'")

        transaction_type = transaction.get("transaction_type")
        if not isinstance(transaction_type, str):
            raise ValueError(
                f"Transaction at index {idx} missing valid 'transaction_type'"
            )
        normalized_type = transaction_type.strip().lower()

        vat_amount = _resolve_vat_amount(transaction)
        if normalized_type in OUTPUT_TRANSACTION_TYPES:
            delta = vat_amount
        elif normalized_type in INPUT_TRANSACTION_TYPES:
            delta = -vat_amount
        else:
            raise ValueError(
                f"Unsupported 'transaction_type' at index {idx}: {transaction_type!r}"
            )

        totals[jurisdiction] = totals.get(jurisdiction, ZERO) + delta

    return {
        jurisdiction: f"{total.quantize(TWOPLACES, rounding=ROUND_HALF_UP):.2f}"
        for jurisdiction, total in sorted(totals.items())
    }


def _read_transactions(input_path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {input_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {input_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Input JSON must be an array of transactions")
    return data


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python vat_calculator.py <transactions.json>", file=sys.stderr)
        return 2

    input_path = Path(argv[1])

    try:
        transactions = _read_transactions(input_path)
        totals = calculate_vat_payable_by_jurisdiction(transactions)
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return 1

    print(json.dumps(totals, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
