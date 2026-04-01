"""Compute VAT payable totals for each jurisdiction.

This module supports a simple transaction model where:
- output VAT (sales) increases VAT payable
- input VAT (purchases) reduces VAT payable

If a transaction has both `vat_collected` and `vat_paid` explicitly,
`vat_collected - vat_paid` is used directly.
Otherwise:
- type == "sale"     -> amount * vat_rate
- type == "purchase" -> -(amount * vat_rate)
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Mapping

CENT = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert input values to Decimal with clear error messages."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _transaction_vat(txn: Mapping[str, Any]) -> Decimal:
    """Return net VAT effect for a single transaction."""
    if "vat_collected" in txn or "vat_paid" in txn:
        vat_collected = _to_decimal(txn.get("vat_collected", 0), "vat_collected")
        vat_paid = _to_decimal(txn.get("vat_paid", 0), "vat_paid")
        return vat_collected - vat_paid

    txn_type = str(txn.get("type", "")).strip().lower()
    if txn_type not in {"sale", "purchase"}:
        raise ValueError(
            "Transaction must include either explicit vat_collected/vat_paid "
            "or a valid 'type' of 'sale'/'purchase'."
        )

    amount = _to_decimal(txn.get("amount", 0), "amount")
    vat_rate = _to_decimal(txn.get("vat_rate", 0), "vat_rate")
    vat_value = amount * vat_rate

    if txn_type == "sale":
        return vat_value
    return -vat_value


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Decimal]:
    """Aggregate VAT payable by jurisdiction.

    Args:
        transactions: Iterable of transaction dicts.

    Returns:
        Dict mapping jurisdiction to VAT payable amount (2dp Decimal).
    """
    totals: Dict[str, Decimal] = {}

    for idx, txn in enumerate(transactions):
        jurisdiction = str(txn.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} is missing 'jurisdiction'.")

        vat_effect = _transaction_vat(txn)
        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + vat_effect

    return {jurisdiction: _round_money(total) for jurisdiction, total in totals.items()}


def vat_payable_json_ready(transactions: Iterable[Mapping[str, Any]]) -> Dict[str, str]:
    """Convenience helper for serialized output."""
    totals = calculate_vat_payable_by_jurisdiction(transactions)
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in totals.items()}


if __name__ == "__main__":
    import json
    import sys

    raw = sys.stdin.read().strip()
    if not raw:
        print(
            "Provide JSON array of transactions on stdin.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    data: List[Dict[str, Any]] = json.loads(raw)
    print(json.dumps(vat_payable_json_ready(data), indent=2, sort_keys=True))
