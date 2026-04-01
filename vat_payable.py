#!/usr/bin/env python3
"""Calculate VAT payable by jurisdiction."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Any


TWO_PLACES = Decimal("0.01")

SALE_DIRECTIONS = {"sale", "sales", "output"}
PURCHASE_DIRECTIONS = {"purchase", "purchases", "input"}


@dataclass
class VatSummary:
    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")

    @property
    def net_vat(self) -> Decimal:
        return self.output_vat - self.input_vat

    @property
    def vat_payable(self) -> Decimal:
        return max(self.net_vat, Decimal("0"))

    @property
    def vat_credit(self) -> Decimal:
        return max(Decimal("0") - self.net_vat, Decimal("0"))


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid value for '{field_name}': {value!r}") from exc


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _direction_bucket(direction: str) -> str:
    normalized = direction.strip().lower()
    if normalized in SALE_DIRECTIONS:
        return "output"
    if normalized in PURCHASE_DIRECTIONS:
        return "input"
    raise ValueError(
        "Invalid direction. Expected one of: "
        f"{sorted(SALE_DIRECTIONS | PURCHASE_DIRECTIONS)}"
    )


def _transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        return abs(vat_amount)

    amount = _to_decimal(transaction["amount"], "amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    return abs(amount * vat_rate)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, str]]:
    """Return VAT summaries keyed by jurisdiction.

    Input transactions must include:
      - jurisdiction (str)
      - direction ("sale"/"output" or "purchase"/"input")
      - either vat_amount, or amount + vat_rate
    """

    summaries: dict[str, VatSummary] = defaultdict(VatSummary)

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction requires a non-empty 'jurisdiction'.")

        direction = str(transaction.get("direction", "")).strip()
        bucket = _direction_bucket(direction)
        vat_value = _transaction_vat(transaction)

        if bucket == "output":
            summaries[jurisdiction].output_vat += vat_value
        else:
            summaries[jurisdiction].input_vat += vat_value

    result: dict[str, dict[str, str]] = {}
    for jurisdiction in sorted(summaries):
        summary = summaries[jurisdiction]
        result[jurisdiction] = {
            "output_vat": str(_round_money(summary.output_vat)),
            "input_vat": str(_round_money(summary.input_vat)),
            "net_vat": str(_round_money(summary.net_vat)),
            "vat_payable": str(_round_money(summary.vat_payable)),
            "vat_credit": str(_round_money(summary.vat_credit)),
        }
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSON file containing a list of transaction objects.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    data = json.loads(args.input_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of transactions.")

    result = calculate_vat_payable_by_jurisdiction(data)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
