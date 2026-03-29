"""VAT payable calculations grouped by jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

_OUTPUT_TYPES = {"sale", "sales", "output", "output_vat"}
_INPUT_TYPES = {"purchase", "purchases", "input", "input_vat"}


def _to_decimal(value: Any) -> Decimal:
    """Convert numeric values to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_currency(value: Decimal) -> Decimal:
    """Round to cents using standard half-up rule."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """
    Calculate VAT payable per jurisdiction.

    The formula used is:
      VAT payable = output VAT - input VAT

    Expected transaction keys:
      - jurisdiction: str
      - vat_amount: number or Decimal
      - type OR transaction_type: one of sale/output or purchase/input variants
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for tx in transactions:
        jurisdiction = tx.get("jurisdiction")
        if not jurisdiction:
            raise ValueError("Transaction is missing required field: jurisdiction")

        if "vat_amount" not in tx:
            raise ValueError("Transaction is missing required field: vat_amount")

        tx_type = str(tx.get("type", tx.get("transaction_type", ""))).strip().lower()
        if tx_type in _OUTPUT_TYPES:
            sign = Decimal("1")
        elif tx_type in _INPUT_TYPES:
            sign = Decimal("-1")
        else:
            raise ValueError(
                "Transaction type must be one of sale/output or purchase/input variants"
            )

        totals[str(jurisdiction)] += sign * _to_decimal(tx["vat_amount"])

    return {
        jurisdiction: _quantize_currency(amount)
        for jurisdiction, amount in totals.items()
    }
