"""Utilities for computing VAT payable by jurisdiction.

The main entry point is :func:`generate_vat_payable_by_jurisdiction`.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

TWOPLACES = Decimal("0.01")
OUTPUT_TYPES = {"sale", "output"}
INPUT_TYPES = {"purchase", "input"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a user provided number into a Decimal."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion path
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _quantize_money(value: Decimal) -> Decimal:
    """Round to two decimal places using standard commercial rounding."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _extract_vat_amount(transaction: dict[str, Any]) -> Decimal:
    """Read VAT amount directly, or derive from amount and VAT rate."""
    if "vat_amount" in transaction:
        vat = _to_decimal(transaction["vat_amount"], "vat_amount")
    else:
        if "amount" not in transaction or "vat_rate" not in transaction:
            raise ValueError(
                "Each transaction must include 'vat_amount' or both "
                "'amount' and 'vat_rate'."
            )
        amount = _to_decimal(transaction["amount"], "amount")
        vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
        vat = amount * vat_rate
    return _quantize_money(vat)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Generate VAT payable for each jurisdiction.

    Args:
        transactions: Iterable of transaction dictionaries. Each transaction
            must include:
              - ``jurisdiction``: jurisdiction name/code (str)
              - ``type``: one of ``sale``/``output`` or ``purchase``/``input``
              - Either ``vat_amount`` OR both ``amount`` and ``vat_rate``

    Returns:
        A dictionary keyed by jurisdiction with values:
            - ``output_vat``: VAT collected on sales
            - ``input_vat``: VAT paid on purchases
            - ``vat_payable``: VAT due for payment (never negative)
            - ``vat_credit``: recoverable VAT credit (never negative)
    """
    output_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    input_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, dict):
            raise ValueError(f"Transaction at index {index} must be a dictionary.")

        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(
                f"Transaction at index {index} is missing a valid 'jurisdiction'."
            )

        tx_type_raw = transaction.get("type")
        if not isinstance(tx_type_raw, str):
            raise ValueError(
                f"Transaction at index {index} is missing a valid 'type'."
            )
        tx_type = tx_type_raw.lower()

        vat_amount = _extract_vat_amount(transaction)
        if vat_amount < 0:
            raise ValueError(f"Transaction at index {index} has a negative VAT amount.")

        if tx_type in OUTPUT_TYPES:
            output_totals[jurisdiction] += vat_amount
        elif tx_type in INPUT_TYPES:
            input_totals[jurisdiction] += vat_amount
        else:
            raise ValueError(
                f"Transaction at index {index} has unsupported type '{tx_type_raw}'. "
                "Use 'sale'/'output' or 'purchase'/'input'."
            )

    jurisdictions = sorted(set(output_totals) | set(input_totals))
    result: dict[str, dict[str, float]] = {}
    for jurisdiction in jurisdictions:
        output_vat = _quantize_money(output_totals[jurisdiction])
        input_vat = _quantize_money(input_totals[jurisdiction])
        net = _quantize_money(output_vat - input_vat)

        vat_payable = net if net > 0 else Decimal("0")
        vat_credit = -net if net < 0 else Decimal("0")

        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
            "vat_credit": float(vat_credit),
        }

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from JSON transactions."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSON file containing a list of transactions.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    with args.input_file.open("r", encoding="utf-8") as infile:
        transactions = json.load(infile)
    output = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
