#!/usr/bin/env python3
"""Generate VAT to be paid (or refunded) for each jurisdiction."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Any) -> Decimal:
    decimal_rate = _to_decimal(rate, "vat_rate")
    if decimal_rate < 0:
        raise ValueError(f"VAT rate cannot be negative: {rate!r}")
    if decimal_rate > 1:
        decimal_rate = decimal_rate / Decimal("100")
    return decimal_rate


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _get_required(transaction: dict[str, Any], key: str) -> Any:
    if key not in transaction:
        raise ValueError(f"Missing required field '{key}' in transaction: {transaction!r}")
    return transaction[key]


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """
    Compute VAT payable/refundable totals for each jurisdiction.

    Expected transaction fields:
      - jurisdiction: str
      - amount: number (taxable amount)
      - vat_rate: number (either 0.2 or 20 for 20%)
      - transaction_type: "sale" or "purchase"
      - deductible: bool (optional; only relevant for purchases, default True)
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "taxable_sales": Decimal("0"),
            "taxable_purchases": Decimal("0"),
            "output_vat": Decimal("0"),
            "input_vat_credit": Decimal("0"),
        }
    )

    for transaction in transactions:
        jurisdiction_raw = _get_required(transaction, "jurisdiction")
        jurisdiction = str(jurisdiction_raw).strip()
        if not jurisdiction:
            raise ValueError(f"Jurisdiction cannot be empty: {transaction!r}")

        amount = _to_decimal(_get_required(transaction, "amount"), "amount")
        if amount < 0:
            raise ValueError(f"Transaction amount cannot be negative: {transaction!r}")

        rate = _normalize_rate(_get_required(transaction, "vat_rate"))
        transaction_type = str(_get_required(transaction, "transaction_type")).strip().lower()

        vat_amount = _quantize_money(amount * rate)
        jurisdiction_totals = totals[jurisdiction]

        if transaction_type == "sale":
            jurisdiction_totals["taxable_sales"] += amount
            jurisdiction_totals["output_vat"] += vat_amount
            continue

        if transaction_type == "purchase":
            jurisdiction_totals["taxable_purchases"] += amount
            if bool(transaction.get("deductible", True)):
                jurisdiction_totals["input_vat_credit"] += vat_amount
            continue

        raise ValueError(
            f"Unsupported transaction_type '{transaction_type}'. "
            "Expected 'sale' or 'purchase'."
        )

    result: dict[str, dict[str, float]] = {}
    for jurisdiction, values in sorted(totals.items()):
        output_vat = _quantize_money(values["output_vat"])
        input_vat_credit = _quantize_money(values["input_vat_credit"])
        net_vat = _quantize_money(output_vat - input_vat_credit)
        vat_payable = _quantize_money(max(net_vat, Decimal("0")))
        vat_refundable = _quantize_money(max(Decimal("0"), -net_vat))

        result[jurisdiction] = {
            "taxable_sales": float(_quantize_money(values["taxable_sales"])),
            "taxable_purchases": float(_quantize_money(values["taxable_purchases"])),
            "output_vat": float(output_vat),
            "input_vat_credit": float(input_vat_credit),
            "net_vat": float(net_vat),
            "vat_payable": float(vat_payable),
            "vat_refundable": float(vat_refundable),
        }

    return result


def _load_transactions(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        transactions = payload
    elif isinstance(payload, dict) and isinstance(payload.get("transactions"), list):
        transactions = payload["transactions"]
    else:
        raise ValueError(
            "Input JSON must be an array of transactions or an object "
            "with a 'transactions' array."
        )

    for item in transactions:
        if not isinstance(item, dict):
            raise ValueError(f"Each transaction must be an object. Found: {item!r}")
    return transactions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transactions JSON."
    )
    parser.add_argument("input_file", type=Path, help="Path to input JSON file")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.input_file)
    report = generate_vat_to_be_paid_by_jurisdiction(transactions)
    if args.pretty:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
