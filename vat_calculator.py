"""Utilities for calculating VAT payable by jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Any

TWOPLACES = Decimal("0.01")
OUTPUT_TYPES = {"sale", "output"}
INPUT_TYPES = {"purchase", "input"}


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert a numeric input to Decimal safely."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _extract_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    """Read VAT amount directly, or compute it from amount * rate."""
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], field_name="vat_amount")
        return _quantize_money(vat_amount)

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction must include 'vat_amount' or both 'amount' and 'vat_rate'."
        )

    amount = _to_decimal(transaction["amount"], field_name="amount")
    vat_rate = _to_decimal(transaction["vat_rate"], field_name="vat_rate")
    return _quantize_money(amount * vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """
    Generate VAT totals by jurisdiction.

    Expected transaction keys:
      - jurisdiction: str
      - transaction_type: one of {'sale', 'output', 'purchase', 'input'}
      - vat_amount OR both amount and vat_rate

    Returns a dictionary keyed by jurisdiction with these totals:
      - output_vat
      - input_vat
      - net_vat
      - vat_payable       (max(net_vat, 0))
      - vat_refundable    (max(-net_vat, 0))
    """
    jurisdiction_totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for idx, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} is missing 'jurisdiction'.")

        tx_type = str(transaction.get("transaction_type", "")).strip().lower()
        if tx_type not in OUTPUT_TYPES | INPUT_TYPES:
            raise ValueError(
                f"Transaction at index {idx} has invalid 'transaction_type': {tx_type!r}."
            )

        vat_amount = _extract_vat_amount(transaction)
        if tx_type in OUTPUT_TYPES:
            jurisdiction_totals[jurisdiction]["output_vat"] += vat_amount
        else:
            jurisdiction_totals[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, totals in jurisdiction_totals.items():
        output_vat = _quantize_money(totals["output_vat"])
        input_vat = _quantize_money(totals["input_vat"])
        net_vat = _quantize_money(output_vat - input_vat)

        vat_payable = net_vat if net_vat > 0 else Decimal("0.00")
        vat_refundable = -net_vat if net_vat < 0 else Decimal("0.00")

        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": _quantize_money(vat_payable),
            "vat_refundable": _quantize_money(vat_refundable),
        }

    return result
