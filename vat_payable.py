"""VAT payable calculator grouped by jurisdiction.

This module computes VAT to be paid for each jurisdiction by aggregating:
- output VAT from sales
- input VAT from purchases

VAT payable = output VAT - input VAT
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert numeric input to Decimal with clear error messages."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Normalize VAT rate so both 0.20 and 20 are accepted."""
    if rate < 0:
        raise ValueError("VAT rate cannot be negative.")
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _resolve_vat_amount(transaction: dict[str, Any]) -> Decimal:
    """Resolve VAT amount from explicit value or taxable amount * rate."""
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        if vat_amount < 0:
            raise ValueError("vat_amount cannot be negative.")
        return vat_amount

    if "net_amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction must provide either 'vat_amount' or both 'net_amount' and 'vat_rate'."
        )

    net_amount = _to_decimal(transaction["net_amount"], "net_amount")
    vat_rate = _normalize_rate(_to_decimal(transaction["vat_rate"], "vat_rate"))

    if net_amount < 0:
        raise ValueError("net_amount cannot be negative.")

    return net_amount * vat_rate


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Aggregate VAT payable per jurisdiction.

    Each transaction must include:
      - jurisdiction: str
      - type: "sale" or "purchase"
      - Either:
          - vat_amount
        or:
          - net_amount and vat_rate

    Returns a dict keyed by jurisdiction with:
      - output_vat
      - input_vat
      - vat_payable (output - input)
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for index, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(f"Transaction at index {index} is missing valid 'jurisdiction'.")

        tx_type = transaction.get("type")
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction at index {index} has invalid 'type': {tx_type!r}. "
                "Expected 'sale' or 'purchase'."
            )

        vat_amount = _resolve_vat_amount(transaction)
        bucket = totals[jurisdiction]
        if tx_type == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    results: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _quantize(totals[jurisdiction]["output_vat"])
        input_vat = _quantize(totals[jurisdiction]["input_vat"])
        results[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _quantize(output_vat - input_vat),
        }

    return results


def _format_for_json(
    result: dict[str, dict[str, Decimal]],
) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {key: f"{value:.2f}" for key, value in values.items()}
        for jurisdiction, values in result.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable grouped by jurisdiction from a JSON transaction file."
    )
    parser.add_argument("input_file", type=Path, help="Path to JSON file with transaction array.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON.",
    )
    args = parser.parse_args()

    transactions = json.loads(args.input_file.read_text(encoding="utf-8"))
    if not isinstance(transactions, list):
        raise ValueError("Input JSON must be an array of transactions.")

    result = generate_vat_payable_by_jurisdiction(transactions)
    output = _format_for_json(result)
    if args.pretty:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
