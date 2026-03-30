"""Utilities for calculating VAT payable by jurisdiction.

VAT payable is calculated as:
    output VAT - input VAT
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


def _to_decimal(value: Any, field_name: str, transaction_index: int) -> Decimal:
    """Convert a numeric-like value into Decimal with helpful errors."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"Transaction {transaction_index}: invalid {field_name!r} value {value!r}"
        ) from exc


def calculate_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Any]],
    *,
    jurisdiction_key: str = "jurisdiction",
    output_vat_key: str = "output_vat",
    input_vat_key: str = "input_vat",
    currency_precision: str = "0.01",
) -> dict[str, Decimal]:
    """Aggregate VAT payable amount for each jurisdiction.

    Args:
        transactions: A list of tax transaction dictionaries.
        jurisdiction_key: The dictionary key used for the jurisdiction name.
        output_vat_key: The dictionary key for output VAT amount.
        input_vat_key: The dictionary key for input VAT amount.
        currency_precision: Decimal quantization unit (default 2 decimals).

    Returns:
        Mapping of jurisdiction -> VAT payable amount as Decimal.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    quantize_unit = Decimal(currency_precision)

    for index, transaction in enumerate(transactions):
        if jurisdiction_key not in transaction:
            raise ValueError(
                f"Transaction {index}: missing required key {jurisdiction_key!r}"
            )
        if output_vat_key not in transaction:
            raise ValueError(
                f"Transaction {index}: missing required key {output_vat_key!r}"
            )
        if input_vat_key not in transaction:
            raise ValueError(
                f"Transaction {index}: missing required key {input_vat_key!r}"
            )

        jurisdiction = str(transaction[jurisdiction_key]).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction {index}: jurisdiction cannot be empty")

        output_vat = _to_decimal(transaction[output_vat_key], output_vat_key, index)
        input_vat = _to_decimal(transaction[input_vat_key], input_vat_key, index)
        totals[jurisdiction] += output_vat - input_vat

    return {
        jurisdiction: amount.quantize(quantize_unit, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in sorted(totals.items())
    }


def _load_transactions(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Input JSON must be a list of transaction objects")

    transactions: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Transaction {idx}: expected object, got {type(item)!r}")
        transactions.append(item)
    return transactions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON file with transactions",
    )
    args = parser.parse_args()

    transactions = _load_transactions(Path(args.input))
    payable = calculate_vat_payable_by_jurisdiction(transactions)

    # Convert Decimal values to string to avoid float precision issues in JSON.
    serializable = {jurisdiction: str(amount) for jurisdiction, amount in payable.items()}
    print(json.dumps(serializable, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
