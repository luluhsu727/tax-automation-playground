"""Utilities to compute VAT payable per jurisdiction.

Core rule:
    VAT payable = Output VAT on sales - Input VAT on purchases

Each transaction is expected to be a mapping with keys:
    jurisdiction (str): country/region tax jurisdiction.
    amount (number | str): net amount before VAT.
    vat_rate (number | str, optional): VAT rate as decimal (0.2) or percent ("20%").
    vat_amount (number | str, optional): explicit VAT amount override.
    transaction_type (str): "sale" or "purchase".
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping
import json
import sys

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a value to Decimal with clear validation errors."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _parse_rate(vat_rate: Any) -> Decimal:
    """Parse a VAT rate provided as decimal or percent string."""
    if vat_rate is None:
        raise ValueError("Missing vat_rate when vat_amount is not provided.")

    if isinstance(vat_rate, str):
        rate_str = vat_rate.strip()
        if rate_str.endswith("%"):
            return _to_decimal(rate_str[:-1], "vat_rate") / Decimal("100")
        return _to_decimal(rate_str, "vat_rate")

    return _to_decimal(vat_rate, "vat_rate")


def _compute_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Compute VAT from either vat_amount or amount * vat_rate."""
    vat_amount = transaction.get("vat_amount")
    if vat_amount is not None:
        return _to_decimal(vat_amount, "vat_amount")

    amount = _to_decimal(transaction.get("amount"), "amount")
    vat_rate = _parse_rate(transaction.get("vat_rate"))
    return amount * vat_rate


def compute_vat_to_be_paid(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """Aggregate VAT payable per jurisdiction.

    Sales add to payable VAT (output VAT) and purchases reduce payable VAT
    (input VAT credit). Values are rounded to 2 decimal places.
    """
    vat_payable_by_jurisdiction: dict[str, Decimal] = {}

    for index, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(f"Invalid jurisdiction at index {index}: {jurisdiction!r}")

        transaction_type = str(transaction.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Invalid transaction_type at index {index}: {transaction_type!r}. "
                "Expected 'sale' or 'purchase'."
            )

        vat_value = _compute_transaction_vat(transaction)
        sign = Decimal("1") if transaction_type == "sale" else Decimal("-1")

        vat_payable_by_jurisdiction[jurisdiction] = (
            vat_payable_by_jurisdiction.get(jurisdiction, Decimal("0"))
            + (sign * vat_value)
        )

    rounded: dict[str, float] = {}
    for jurisdiction, amount in vat_payable_by_jurisdiction.items():
        rounded[jurisdiction] = float(amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP))

    return rounded


def _main(argv: list[str]) -> int:
    """CLI usage: python vat_calculator.py path/to/transactions.json."""
    if len(argv) != 2:
        print("Usage: python vat_calculator.py <transactions.json>", file=sys.stderr)
        return 2

    with open(argv[1], "r", encoding="utf-8") as file_obj:
        transactions = json.load(file_obj)

    result = compute_vat_to_be_paid(transactions)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
