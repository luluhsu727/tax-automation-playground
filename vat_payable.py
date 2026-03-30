"""Compute VAT payable amounts by jurisdiction.

The core function, ``generate_vat_payable_by_jurisdiction``, accepts transaction
records and returns totals per jurisdiction.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a value to Decimal and raise a clear error on invalid input."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Generate VAT totals and net payable amount per jurisdiction.

    Each record must include:
      - jurisdiction: string
      - output_vat: numeric (VAT charged on sales)
      - input_vat: numeric (VAT paid on purchases)

    Returns a dictionary keyed by jurisdiction with stringified decimal values:
      {
        "DE": {
          "output_vat": "150.00",
          "input_vat": "30.00",
          "vat_payable": "120.00"
        }
      }
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for idx, record in enumerate(records):
        if "jurisdiction" not in record:
            raise ValueError(f"Record at index {idx} is missing 'jurisdiction'")
        jurisdiction = str(record["jurisdiction"]).strip()
        if not jurisdiction:
            raise ValueError(f"Record at index {idx} has an empty 'jurisdiction'")

        if "output_vat" not in record:
            raise ValueError(f"Record at index {idx} is missing 'output_vat'")
        if "input_vat" not in record:
            raise ValueError(f"Record at index {idx} is missing 'input_vat'")

        output_vat = _to_decimal(record["output_vat"], "output_vat")
        input_vat = _to_decimal(record["input_vat"], "input_vat")

        totals[jurisdiction]["output_vat"] += output_vat
        totals[jurisdiction]["input_vat"] += input_vat

    result: dict[str, dict[str, str]] = {}
    for jurisdiction, values in sorted(totals.items()):
        output_total = _quantize(values["output_vat"])
        input_total = _quantize(values["input_vat"])
        payable = _quantize(output_total - input_total)
        result[jurisdiction] = {
            "output_vat": str(output_total),
            "input_vat": str(input_total),
            "vat_payable": str(payable),
        }

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amounts for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON file containing a list of VAT records.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("Input JSON must be a list of records.")

    result = generate_vat_payable_by_jurisdiction(records)
    if args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
