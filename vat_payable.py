"""Compute VAT payable amounts per jurisdiction.

This module provides a small, dependency-free API for calculating VAT
obligations by jurisdiction from transaction-level data.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Any, Dict, Iterable, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert an incoming value to Decimal with clear validation errors."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Any) -> Decimal:
    """Normalize VAT rate to decimal fraction.

    Accepts either fractional rates (0.2 for 20%) or percentage points
    (20 for 20%).
    """
    vat_rate = _to_decimal(rate, field_name="vat_rate")
    if vat_rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if vat_rate <= Decimal("1"):
        return vat_rate
    if vat_rate <= Decimal("100"):
        return vat_rate / Decimal("100")
    raise ValueError("vat_rate must be a decimal fraction or percentage <= 100")


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass
class _Accumulator:
    taxable_sales: Decimal = Decimal("0")
    taxable_purchases: Decimal = Decimal("0")
    output_vat: Decimal = Decimal("0")
    input_vat_recoverable: Decimal = Decimal("0")

    def summary(self) -> Dict[str, Decimal]:
        net_vat = self.output_vat - self.input_vat_recoverable
        vat_payable = net_vat if net_vat > 0 else Decimal("0")
        vat_credit = -net_vat if net_vat < 0 else Decimal("0")
        return {
            "taxable_sales": _q(self.taxable_sales),
            "taxable_purchases": _q(self.taxable_purchases),
            "output_vat": _q(self.output_vat),
            "input_vat_recoverable": _q(self.input_vat_recoverable),
            "net_vat": _q(net_vat),
            "vat_payable": _q(vat_payable),
            "vat_credit": _q(vat_credit),
        }


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Decimal]]:
    """Aggregate VAT metrics per jurisdiction.

    Required transaction keys:
      - jurisdiction: string
      - type: "sale" or "purchase"
      - amount: taxable amount (non-negative number)
      - vat_rate: VAT rate as fraction (e.g. 0.2) or percentage (e.g. 20)

    Optional transaction keys:
      - input_vat_recoverable: bool, defaults to True for purchase transactions.
    """
    buckets: Dict[str, _Accumulator] = defaultdict(_Accumulator)

    for idx, txn in enumerate(transactions):
        jurisdiction = str(txn.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} has no jurisdiction")

        txn_type = str(txn.get("type", "")).strip().lower()
        if txn_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction at index {idx} has invalid type: {txn.get('type')!r}"
            )

        amount = _to_decimal(txn.get("amount"), field_name="amount")
        if amount < 0:
            raise ValueError(f"Transaction at index {idx} has negative amount")

        rate = _normalize_rate(txn.get("vat_rate"))
        vat_amount = amount * rate

        bucket = buckets[jurisdiction]
        if txn_type == "sale":
            bucket.taxable_sales += amount
            bucket.output_vat += vat_amount
            continue

        # Purchase transaction
        bucket.taxable_purchases += amount
        recoverable = txn.get("input_vat_recoverable", True)
        if recoverable:
            bucket.input_vat_recoverable += vat_amount

    return {j: data.summary() for j, data in sorted(buckets.items())}


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Decimal]]:
    """Alias for the primary API name used by callers."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def _decimal_map_to_float(data: Mapping[str, Mapping[str, Decimal]]) -> Dict[str, Dict[str, float]]:
    return {
        jurisdiction: {key: float(value) for key, value in summary.items()}
        for jurisdiction, summary in data.items()
    }


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate VAT payable amounts per jurisdiction from JSON input."
    )
    parser.add_argument("input_file", help="Path to a JSON file containing transactions")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print output JSON",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict) and "transactions" in payload:
        transactions = payload["transactions"]
    else:
        transactions = payload

    result = generate_vat_payable_by_jurisdiction(transactions)
    out = _decimal_map_to_float(result)
    if args.pretty:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(json.dumps(out, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
