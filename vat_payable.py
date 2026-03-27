"""Compatibility script/module for VAT payable aggregation.

This file exists for historical task variants that execute:
    python vat_payable.py <input.json>
or import helpers from module-level ``vat_payable``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vat_payable import (
    Transaction,
    _format_report,
    calculate_vat_payable_by_jurisdiction,
    load_transactions,
    transaction_from_record,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to input JSON transaction file")
    parser.add_argument(
        "--floor-at-zero",
        action="store_true",
        help="Set negative net VAT values to 0.00",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON object instead of plain text",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.input_file)
    vat_by_jurisdiction = calculate_vat_payable_by_jurisdiction(
        transactions, floor_at_zero=args.floor_at_zero
    )

    if args.json:
        payload = {k: f"{v:.2f}" for k, v in sorted(vat_by_jurisdiction.items())}
        print(json.dumps(payload, indent=2))
    else:
        print(_format_report(vat_by_jurisdiction))


__all__ = [
    "Transaction",
    "calculate_vat_payable_by_jurisdiction",
    "load_transactions",
    "transaction_from_record",
]


if __name__ == "__main__":
    main()
