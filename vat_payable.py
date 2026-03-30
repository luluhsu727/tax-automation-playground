"""Compute VAT payable per jurisdiction from transaction data.

The main entry point is ``generate_vat_to_be_paid_by_jurisdiction`` which
accepts transaction dictionaries and returns a per-jurisdiction breakdown.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


TWOPLACES = Decimal("0.01")


def _to_decimal(value: object) -> Decimal:
    """Convert incoming numeric-ish values to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise TypeError(f"Unsupported numeric value: {value!r}")


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_transaction_type(raw_type: str) -> str:
    normalized = raw_type.strip().lower()
    aliases = {
        "sale": "sale",
        "sales": "sale",
        "output": "sale",
        "purchase": "purchase",
        "purchases": "purchase",
        "input": "purchase",
    }
    if normalized not in aliases:
        raise ValueError(
            "transaction_type must be one of sale/sales/output/"
            "purchase/purchases/input"
        )
    return aliases[normalized]


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[dict],
) -> dict[str, dict[str, float]]:
    """Generate VAT figures per jurisdiction.

    Each transaction must have:
      - jurisdiction (str)
      - taxable_amount (number)
      - vat_rate (number, e.g. 0.2 for 20%)
      - transaction_type (sale or purchase; aliases are accepted)

    Returns:
      {
        "<jurisdiction>": {
          "output_vat": <float>,
          "input_vat": <float>,
          "vat_to_be_paid": <float>,
          "vat_credit": <float>
        },
        ...
      }
    """
    accumulator: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for idx, txn in enumerate(transactions):
        if not isinstance(txn, dict):
            raise TypeError(f"Transaction at index {idx} must be a dictionary")

        missing = [
            key
            for key in ("jurisdiction", "taxable_amount", "vat_rate", "transaction_type")
            if key not in txn
        ]
        if missing:
            raise ValueError(
                f"Transaction at index {idx} is missing required fields: {missing}"
            )

        jurisdiction = str(txn["jurisdiction"]).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} has empty jurisdiction")

        taxable_amount = _to_decimal(txn["taxable_amount"])
        vat_rate = _to_decimal(txn["vat_rate"])
        if taxable_amount < 0:
            raise ValueError(
                f"Transaction at index {idx} has negative taxable_amount: {taxable_amount}"
            )
        if vat_rate < 0:
            raise ValueError(f"Transaction at index {idx} has negative vat_rate: {vat_rate}")

        vat_value = taxable_amount * vat_rate
        txn_type = _normalize_transaction_type(str(txn["transaction_type"]))

        if txn_type == "sale":
            accumulator[jurisdiction]["output_vat"] += vat_value
        else:
            accumulator[jurisdiction]["input_vat"] += vat_value

    result: dict[str, dict[str, float]] = {}
    for jurisdiction, totals in sorted(accumulator.items()):
        output_vat = _round_money(totals["output_vat"])
        input_vat = _round_money(totals["input_vat"])
        net = output_vat - input_vat
        vat_to_be_paid = _round_money(net if net > 0 else Decimal("0"))
        vat_credit = _round_money(-net if net < 0 else Decimal("0"))

        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_to_be_paid": float(vat_to_be_paid),
            "vat_credit": float(vat_credit),
        }

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid per jurisdiction from JSON transactions."
    )
    parser.add_argument(
        "input",
        help="Path to JSON file containing an array of transactions.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        transactions = json.load(f)

    result = generate_vat_to_be_paid_by_jurisdiction(transactions)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
