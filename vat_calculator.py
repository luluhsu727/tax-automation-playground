"""Utilities for computing VAT payable per jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

MONEY_PLACES = Decimal("0.01")
ONE_HUNDRED = Decimal("100")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Safely convert numeric-like values to Decimal."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """
    Normalize VAT rates to decimal form.

    Examples:
    - 0.2  -> 0.2 (already decimal)
    - 20   -> 0.2 (percentage form)
    """
    if rate < 0:
        raise ValueError("VAT rate cannot be negative.")
    if rate > 1:
        return rate / ONE_HUNDRED
    return rate


def _round_money(value: Decimal) -> Decimal:
    """Round to two decimal places using standard accounting rounding."""
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """
    Generate VAT to be paid for each jurisdiction.

    Input transaction fields:
    - jurisdiction (str): Country/region tax jurisdiction (required)
    - amount (number-like): Taxable base amount (required)
    - vat_rate (number-like): VAT rate, either decimal (0.2) or percent (20) (required)
    - kind (str): "sale" or "purchase" (optional; default "sale")
    - is_vat_deductible (bool): only for purchases; default True

    Rules:
    - Sales increase VAT payable.
    - Deductible purchases decrease VAT payable.
    - Non-deductible purchases do not reduce VAT payable.
    """
    vat_balance_by_jurisdiction: dict[str, Decimal] = defaultdict(Decimal)

    for idx, tx in enumerate(transactions):
        jurisdiction = str(tx.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(
                f"Transaction at index {idx} is missing a non-empty 'jurisdiction'."
            )

        amount = _to_decimal(tx.get("amount"), "amount")
        if amount < 0:
            raise ValueError(f"Transaction at index {idx} has a negative 'amount'.")

        rate = _normalize_rate(_to_decimal(tx.get("vat_rate"), "vat_rate"))

        kind = str(tx.get("kind", "sale")).strip().lower()
        vat_amount = _round_money(amount * rate)

        if kind == "sale":
            vat_balance_by_jurisdiction[jurisdiction] += vat_amount
        elif kind == "purchase":
            if bool(tx.get("is_vat_deductible", True)):
                vat_balance_by_jurisdiction[jurisdiction] -= vat_amount
        else:
            raise ValueError(
                f"Transaction at index {idx} has invalid 'kind': {kind!r}. "
                "Use 'sale' or 'purchase'."
            )

    return {
        jurisdiction: float(_round_money(balance))
        for jurisdiction, balance in sorted(vat_balance_by_jurisdiction.items())
    }


def generate_vat_to_be_paid_per_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """Backward-friendly alias focused on VAT payable wording."""
    return generate_vat_payable_by_jurisdiction(transactions)

