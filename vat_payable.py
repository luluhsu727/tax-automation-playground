"""Utilities to compute VAT payable per jurisdiction.

The main entry point is ``calculate_vat_payable_by_jurisdiction``.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
import argparse
import json
from pathlib import Path
from typing import Any, Iterable


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Convert numbers/strings to Decimal safely."""
    return Decimal(str(value))


def _normalize_rate(rate: Any) -> Decimal:
    """Accept VAT rates as percentages (20) or decimal fractions (0.2)."""
    decimal_rate = _to_decimal(rate)
    if decimal_rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if decimal_rate > 1:
        decimal_rate = decimal_rate / Decimal("100")
    return decimal_rate


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Calculate net VAT payable grouped by jurisdiction.

    Expected transaction fields:
    - jurisdiction (str): jurisdiction identifier (e.g. country code)
    - amount (number): taxable amount
    - vat_rate (number): VAT rate as decimal (0.2) or percent (20)
    - transaction_type (optional str): "sale" or "purchase". Defaults to "sale".
      Purchase VAT is treated as deductible (subtracted from payable VAT).
    - vat_amount (optional number): if present, uses this VAT amount directly.

    Returns:
        dict[str, float]: net VAT payable per jurisdiction, rounded to 2 decimals.
    """

    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions):
        if "jurisdiction" not in transaction:
            raise ValueError(f"transaction at index {index} is missing jurisdiction")

        jurisdiction = str(transaction["jurisdiction"]).strip()
        if not jurisdiction:
            raise ValueError(f"transaction at index {index} has empty jurisdiction")

        tx_type = str(transaction.get("transaction_type", "sale")).strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"transaction at index {index} has invalid transaction_type: {tx_type}"
            )

        if "vat_amount" in transaction and transaction["vat_amount"] is not None:
            vat_amount = _to_decimal(transaction["vat_amount"])
        else:
            if "amount" not in transaction:
                raise ValueError(f"transaction at index {index} is missing amount")
            if "vat_rate" not in transaction:
                raise ValueError(f"transaction at index {index} is missing vat_rate")
            amount = _to_decimal(transaction["amount"])
            rate = _normalize_rate(transaction["vat_rate"])
            vat_amount = amount * rate

        vat_amount = _quantize(vat_amount)
        if tx_type == "purchase":
            vat_amount = -vat_amount

        totals[jurisdiction] += vat_amount

    return {
        jurisdiction: float(_quantize(total))
        for jurisdiction, total in sorted(totals.items(), key=lambda item: item[0])
    }


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Alias for backwards/semantic compatibility."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def generate_vat_to_be_paid_per_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Alias matching alternate phrasing of the same task."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount per jurisdiction from transaction data."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to a JSON file containing an array of transaction objects.",
    )
    args = parser.parse_args()

    with args.input_json.open(encoding="utf-8") as file:
        transactions = json.load(file)

    result = calculate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
