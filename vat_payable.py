"""Utilities for calculating VAT payable per jurisdiction.

VAT payable is calculated as:
    output VAT - input VAT

Where:
  - output VAT is VAT collected on sales
  - input VAT is VAT paid on purchases
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, Mapping


def _to_decimal(value: object, field_name: str) -> Decimal:
    """Convert a numeric input to Decimal with clear errors."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_transaction(transaction: Mapping[str, object]) -> Dict[str, object]:
    """Validate and normalize a transaction dictionary."""
    if "jurisdiction" not in transaction:
        raise ValueError("Each transaction must include 'jurisdiction'")
    if "type" not in transaction:
        raise ValueError("Each transaction must include 'type'")
    if "vat" not in transaction:
        raise ValueError("Each transaction must include 'vat'")

    jurisdiction = str(transaction["jurisdiction"]).strip()
    if not jurisdiction:
        raise ValueError("'jurisdiction' cannot be empty")

    txn_type = str(transaction["type"]).strip().lower()
    if txn_type not in {"sale", "purchase"}:
        raise ValueError("'type' must be either 'sale' or 'purchase'")

    vat = _to_decimal(transaction["vat"], "vat")

    return {
        "jurisdiction": jurisdiction,
        "type": txn_type,
        "vat": vat,
    }


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, Decimal]:
    """Compute VAT payable per jurisdiction.

    Args:
        transactions: Iterable of dictionaries with keys:
            - jurisdiction: str
            - type: "sale" or "purchase"
            - vat: number-like

    Returns:
        Dict mapping jurisdiction -> VAT payable (Decimal).
    """
    output_vat = defaultdict(lambda: Decimal("0"))
    input_vat = defaultdict(lambda: Decimal("0"))

    for transaction in transactions:
        normalized = _normalize_transaction(transaction)
        jurisdiction = normalized["jurisdiction"]
        txn_type = normalized["type"]
        vat = normalized["vat"]

        if txn_type == "sale":
            output_vat[jurisdiction] += vat
        else:
            input_vat[jurisdiction] += vat

    jurisdictions = set(output_vat) | set(input_vat)
    return {
        jurisdiction: output_vat[jurisdiction] - input_vat[jurisdiction]
        for jurisdiction in sorted(jurisdictions)
    }
