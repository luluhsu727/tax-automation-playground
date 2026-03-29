"""Generate VAT to be paid for each jurisdiction."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

TWOPLACES = Decimal("0.01")
VALID_TRANSACTION_TYPES = {"sale", "purchase"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {value!r}") from exc


def _normalize_rate(rate: Any) -> Decimal:
    decimal_rate = _to_decimal(rate, "vat_rate")
    if decimal_rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if decimal_rate > 1:
        decimal_rate = decimal_rate / Decimal("100")
    return decimal_rate


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _read_jurisdiction(transaction: dict[str, Any], index: int) -> str:
    raw = transaction.get("jurisdiction", transaction.get("country"))
    jurisdiction = str(raw or "").strip()
    if not jurisdiction:
        raise ValueError(
            f"transaction at index {index} is missing jurisdiction/country"
        )
    return jurisdiction


def _read_transaction_type(transaction: dict[str, Any], index: int) -> str:
    tx_type = str(transaction.get("transaction_type", "sale")).strip().lower()
    if tx_type not in VALID_TRANSACTION_TYPES:
        raise ValueError(
            f"transaction at index {index} has invalid transaction_type: {tx_type}"
        )
    return tx_type


def _read_vat_amount(transaction: dict[str, Any], index: int) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
    else:
        if "amount" in transaction:
            amount_key = "amount"
        elif "net_amount" in transaction:
            amount_key = "net_amount"
        else:
            raise ValueError(f"transaction at index {index} is missing amount/net_amount")

        if "vat_rate" not in transaction:
            raise ValueError(f"transaction at index {index} is missing vat_rate")

        amount = _to_decimal(transaction[amount_key], amount_key)
        if amount < 0:
            raise ValueError(f"transaction at index {index} has negative {amount_key}")
        vat_amount = amount * _normalize_rate(transaction["vat_rate"])

    if vat_amount < 0:
        raise ValueError(f"transaction at index {index} has negative vat_amount")

    return _to_money(vat_amount)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Return net VAT payable per jurisdiction.

    VAT payable is computed as:
      output VAT (sales) - input VAT (purchases)
    """

    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions):
        jurisdiction = _read_jurisdiction(transaction, index)
        tx_type = _read_transaction_type(transaction, index)
        vat_amount = _read_vat_amount(transaction, index)

        if tx_type == "purchase":
            vat_amount = -vat_amount

        totals[jurisdiction] += vat_amount

    return {
        jurisdiction: float(_to_money(total))
        for jurisdiction, total in sorted(totals.items(), key=lambda item: item[0])
    }


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Alias kept for semantic compatibility."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def generate_vat_to_be_paid_per_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Alias for alternate phrasing of the same requirement."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Alias for alternate phrasing of the same requirement."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to a JSON file containing transaction objects.",
    )
    args = parser.parse_args()

    with args.input_json.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of transaction objects")

    result = calculate_vat_payable_by_jurisdiction(payload)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
