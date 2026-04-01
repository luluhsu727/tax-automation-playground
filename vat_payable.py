"""Utilities to compute VAT payable per jurisdiction.

The core idea:
- Output VAT comes from sales.
- Input VAT comes from purchases.
- VAT payable = output VAT - input VAT (can be negative if refundable).
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Convert numeric-like values to Decimal safely."""
    return Decimal(str(value))


def _compute_vat_amount(transaction: dict[str, Any]) -> Decimal:
    """Return VAT amount from explicit value or net_amount * vat_rate."""
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return _to_decimal(transaction["vat_amount"])

    net_amount = _to_decimal(transaction.get("net_amount", 0))
    vat_rate = _to_decimal(transaction.get("vat_rate", 0))
    return net_amount * vat_rate


def generate_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Aggregate VAT figures by jurisdiction.

    Required per transaction:
    - jurisdiction: str
    - transaction_type: "sale" or "purchase"

    Optional:
    - vat_amount: direct VAT amount for the row
    - net_amount + vat_rate: used when vat_amount is absent
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
            "vat_payable": Decimal("0"),
        }
    )

    for tx in transactions:
        jurisdiction = tx.get("jurisdiction")
        if not jurisdiction:
            raise ValueError("Each transaction must include 'jurisdiction'.")

        transaction_type = tx.get("transaction_type")
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                "Each transaction must include transaction_type "
                "as 'sale' or 'purchase'."
            )

        vat_amount = _compute_vat_amount(tx)
        bucket = totals[jurisdiction]

        if transaction_type == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    for jurisdiction in totals:
        output_vat = totals[jurisdiction]["output_vat"]
        input_vat = totals[jurisdiction]["input_vat"]
        totals[jurisdiction]["vat_payable"] = output_vat - input_vat

        # Keep money representation stable for reporting/exports.
        totals[jurisdiction]["output_vat"] = output_vat.quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        totals[jurisdiction]["input_vat"] = input_vat.quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        totals[jurisdiction]["vat_payable"] = totals[jurisdiction][
            "vat_payable"
        ].quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    return dict(totals)


def _as_json_ready(
    result: dict[str, dict[str, Decimal]],
) -> dict[str, dict[str, str]]:
    """Convert Decimal values into JSON-safe strings."""
    return {
        jurisdiction: {k: format(v, "f") for k, v in metrics.items()}
        for jurisdiction, metrics in result.items()
    }


def main() -> int:
    """CLI entrypoint.

    Usage:
        python vat_payable.py /path/to/transactions.json
    """
    if len(sys.argv) != 2:
        print("Usage: python vat_payable.py <transactions.json>")
        return 1

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as f:
        transactions = json.load(f)

    result = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(_as_json_ready(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
