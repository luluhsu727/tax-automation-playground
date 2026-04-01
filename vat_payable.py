#!/usr/bin/env python3
"""Generate VAT to be paid for each jurisdiction."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping

TWO_DP = Decimal("0.01")


def _to_decimal(value: object, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise TypeError(f"Unsupported numeric value for {field_name!r}: {value!r}")


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWO_DP, rounding=ROUND_HALF_UP)


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, Decimal]:
    """Return net VAT payable by jurisdiction.

    Required fields per transaction:
      - jurisdiction: str
      - amount_ex_vat: decimal-compatible value
      - vat_rate: decimal-compatible value
      - transaction_type: "sale" or "purchase"

    For each transaction:
      vat_amount = amount_ex_vat * vat_rate
      sale     -> adds vat_amount
      purchase -> subtracts vat_amount
    """
    totals: dict[str, Decimal] = {}

    for row in transactions:
        jurisdiction = str(row.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Jurisdiction must be non-empty")

        vat_rate = _to_decimal(row.get("vat_rate"), "vat_rate")
        if vat_rate < 0:
            raise ValueError("VAT rate cannot be negative")

        amount_ex_vat = _to_decimal(row.get("amount_ex_vat"), "amount_ex_vat")
        if amount_ex_vat < 0:
            raise ValueError("Amount excluding VAT cannot be negative")

        vat_amount = _quantize_money(amount_ex_vat * vat_rate)

        transaction_type = str(row.get("transaction_type", "")).strip().lower()
        if transaction_type == "sale":
            signed_vat = vat_amount
        elif transaction_type == "purchase":
            signed_vat = -vat_amount
        else:
            raise ValueError(
                f"Unsupported transaction_type {transaction_type!r}; "
                "use 'sale' or 'purchase'"
            )

        totals[jurisdiction] = _quantize_money(
            totals.get(jurisdiction, Decimal("0.00")) + signed_vat
        )

    return dict(sorted(totals.items(), key=lambda item: item[0]))


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, Decimal]:
    """Alias for alternate naming."""
    return generate_vat_to_be_paid_for_each_jurisdiction(transactions)


def _load_transactions(path: str) -> list[Mapping[str, object]]:
    with open(path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transaction objects")
    return payload


def _to_json_friendly(totals: Mapping[str, Decimal]) -> dict[str, str]:
    return {k: f"{_quantize_money(v):.2f}" for k, v in totals.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "transactions_json",
        help="Path to JSON file containing transaction objects",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.transactions_json)
    totals = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    print(json.dumps(_to_json_friendly(totals), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
