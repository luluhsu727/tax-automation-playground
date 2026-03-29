"""VAT payable calculator per jurisdiction.

This module computes net VAT payable for each jurisdiction from transaction
records. It supports two transaction formats:

1) Explicit VAT amounts:
   {
       "jurisdiction": "DE",
       "output_vat": 120.00,  # VAT collected on sales
       "input_vat": 40.00     # VAT paid on purchases
   }

2) Transaction type with taxable amount and VAT rate:
   {
       "jurisdiction": "FR",
       "transaction_type": "sale",  # "sale" or "purchase"
       "amount": 1000.00,
       "vat_rate": 0.20
   }

Per jurisdiction, VAT payable is:
    total_output_vat - total_input_vat
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert value into Decimal with consistent validation."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_vat_fields(transaction: Mapping[str, Any]) -> tuple[str, Decimal, Decimal]:
    """Return (jurisdiction, output_vat, input_vat) for a transaction."""
    jurisdiction = transaction.get("jurisdiction")
    if not jurisdiction or not isinstance(jurisdiction, str):
        raise ValueError("Each transaction must include a non-empty string 'jurisdiction'.")

    if "output_vat" in transaction or "input_vat" in transaction:
        output_vat = _to_decimal(transaction.get("output_vat", 0), "output_vat")
        input_vat = _to_decimal(transaction.get("input_vat", 0), "input_vat")
        return jurisdiction, output_vat, input_vat

    transaction_type = transaction.get("transaction_type")
    amount = transaction.get("amount")
    vat_rate = transaction.get("vat_rate")

    if transaction_type not in {"sale", "purchase"}:
        raise ValueError(
            "Transaction must provide either explicit VAT fields or "
            "'transaction_type' as 'sale'/'purchase'."
        )
    if amount is None or vat_rate is None:
        raise ValueError("Transactions with 'transaction_type' must include 'amount' and 'vat_rate'.")

    vat_value = _to_decimal(amount, "amount") * _to_decimal(vat_rate, "vat_rate")
    if transaction_type == "sale":
        return jurisdiction, vat_value, Decimal("0")
    return jurisdiction, Decimal("0"), vat_value


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    clamp_negative_to_zero: bool = False,
) -> Dict[str, Dict[str, float]]:
    """Compute VAT summary by jurisdiction.

    Args:
        transactions:
            Iterable of transaction mappings. See module docstring for accepted
            formats.
        clamp_negative_to_zero:
            If True, negative net VAT (credit/refund position) is returned as 0
            for vat_payable only. Output/input totals are unchanged.

    Returns:
        Mapping of jurisdiction -> summary dict:
            {
                "output_vat": <float>,
                "input_vat": <float>,
                "vat_payable": <float>
            }
    """
    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for transaction in transactions:
        jurisdiction, output_vat, input_vat = _normalize_vat_fields(transaction)
        totals[jurisdiction]["output_vat"] += output_vat
        totals[jurisdiction]["input_vat"] += input_vat

    result: Dict[str, Dict[str, float]] = {}
    for jurisdiction, values in totals.items():
        output_vat = values["output_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        input_vat = values["input_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        vat_payable = (output_vat - input_vat).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        if clamp_negative_to_zero and vat_payable < 0:
            vat_payable = Decimal("0.00")

        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }

    return result
