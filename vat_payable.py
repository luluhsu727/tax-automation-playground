"""Generate VAT to be paid for each jurisdiction.

This module aggregates transaction-level VAT effects into jurisdiction totals.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping

CENT = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert an input value to Decimal with a clear error."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _transaction_vat_effect(transaction: Mapping[str, Any]) -> Decimal:
    """Compute VAT effect for one transaction.

    Supported inputs:
    - Explicit VAT fields: vat_collected / vat_paid (used directly if either exists)
    - Type-driven fields: type in {'sale', 'purchase'} with amount and vat_rate
    """
    if "vat_collected" in transaction or "vat_paid" in transaction:
        vat_collected = _to_decimal(transaction.get("vat_collected", 0), "vat_collected")
        vat_paid = _to_decimal(transaction.get("vat_paid", 0), "vat_paid")
        return vat_collected - vat_paid

    transaction_type = str(transaction.get("type", "")).strip().lower()
    if transaction_type not in {"sale", "purchase"}:
        raise ValueError(
            "Transaction must include either explicit vat_collected/vat_paid "
            "or a valid 'type' of 'sale'/'purchase'."
        )

    amount = _to_decimal(transaction.get("amount", 0), "amount")
    vat_rate = _to_decimal(transaction.get("vat_rate", 0), "vat_rate")
    vat_amount = amount * vat_rate
    return vat_amount if transaction_type == "sale" else -vat_amount


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Decimal]:
    """Return VAT payable totals by jurisdiction."""
    totals: Dict[str, Decimal] = {}

    for idx, transaction in enumerate(transactions):
        jurisdiction = str(transaction.get("jurisdiction", "")).strip().upper()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} is missing 'jurisdiction'.")

        vat_effect = _transaction_vat_effect(transaction)
        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + vat_effect

    return {jurisdiction: _round_money(total) for jurisdiction, total in totals.items()}


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Decimal]:
    """Alias for readability with business wording."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def vat_payable_json_ready(transactions: Iterable[Mapping[str, Any]]) -> Dict[str, str]:
    """Return stringified values suitable for JSON serialization."""
    totals = calculate_vat_payable_by_jurisdiction(transactions)
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in totals.items()}
