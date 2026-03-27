"""VAT payable calculator grouped by jurisdiction.

This module computes net VAT due per jurisdiction:
    VAT payable = output VAT on sales - input VAT on purchases
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: object) -> Decimal:
    """Convert a numeric-like value to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_money(amount: Decimal) -> Decimal:
    """Round amounts to currency precision (2 decimal places)."""
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, Decimal]:
    """Generate VAT payable for each jurisdiction.

    Expected transaction fields:
      - jurisdiction: str
      - type: "sale" or "purchase"
      - amount: numeric (taxable amount)
      - vat_rate: numeric (e.g. 0.20 for 20%)

    Returns:
      Dict[jurisdiction, vat_payable]
    """

    vat_payable: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for tx in transactions:
        jurisdiction = str(tx["jurisdiction"])
        tx_type = str(tx["type"]).lower()
        amount = _to_decimal(tx["amount"])
        vat_rate = _to_decimal(tx["vat_rate"])
        vat_amount = _round_money(amount * vat_rate)

        if tx_type == "sale":
            vat_payable[jurisdiction] += vat_amount
        elif tx_type == "purchase":
            vat_payable[jurisdiction] -= vat_amount
        else:
            raise ValueError(f"Unknown transaction type: {tx_type}")

    return {k: _round_money(v) for k, v in sorted(vat_payable.items())}


def vat_payable_to_json_ready(vat_payable: Mapping[str, Decimal]) -> Dict[str, str]:
    """Convert Decimal values to string values for JSON output."""
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in vat_payable.items()}


def _load_transactions(input_path: str | None) -> list[dict[str, object]]:
    """Load transactions from JSON file path or stdin."""
    if input_path:
        with open(input_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    else:
        payload = json.load(sys.stdin)

    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON array of transaction objects.")

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable grouped by jurisdiction."
    )
    parser.add_argument(
        "--input",
        help="Path to a JSON file containing transaction rows. If omitted, reads stdin.",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.input)
    vat_payable = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(vat_payable_to_json_ready(vat_payable), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
