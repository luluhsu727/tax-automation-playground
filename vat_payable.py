"""Utilities for calculating VAT payable by jurisdiction.

The core function in this module expects a list of transaction records and
returns payable VAT totals grouped by jurisdiction.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping


MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """Represents a VAT-relevant transaction."""

    jurisdiction: str
    net_amount: Decimal
    vat_rate: Decimal
    transaction_type: str
    vat_amount: Decimal | None = None


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion branch
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Support rates as fractions (0.2) or percentages (20)."""
    if rate < 0:
        raise ValueError("vat_rate must not be negative")
    if rate > 1:
        return (rate / Decimal("100")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return rate


def _normalize_transaction(raw: Mapping[str, object]) -> Transaction:
    jurisdiction = str(raw.get("jurisdiction", "")).strip()
    if not jurisdiction:
        raise ValueError("jurisdiction is required")

    transaction_type = str(raw.get("transaction_type", "")).strip().lower()
    if transaction_type not in {"sale", "purchase"}:
        raise ValueError("transaction_type must be either 'sale' or 'purchase'")

    net_amount = _to_decimal(raw.get("net_amount"), "net_amount")
    if net_amount < 0:
        raise ValueError("net_amount must not be negative")

    vat_rate = _normalize_rate(_to_decimal(raw.get("vat_rate"), "vat_rate"))
    vat_amount_raw = raw.get("vat_amount")
    vat_amount = None if vat_amount_raw is None else _to_decimal(vat_amount_raw, "vat_amount")

    return Transaction(
        jurisdiction=jurisdiction,
        net_amount=net_amount,
        vat_rate=vat_rate,
        transaction_type=transaction_type,
        vat_amount=vat_amount,
    )


def _transaction_vat_amount(txn: Transaction) -> Decimal:
    if txn.vat_amount is not None:
        if txn.vat_amount < 0:
            raise ValueError("vat_amount must not be negative")
        return txn.vat_amount
    return txn.net_amount * txn.vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
    *,
    round_to_cents: bool = True,
) -> dict[str, Decimal]:
    """Calculate payable VAT totals grouped by jurisdiction.

    Args:
        transactions: iterable of mappings with these keys:
            - jurisdiction (str): e.g. "DE", "UK", "CA-ON"
            - net_amount (number-like)
            - vat_rate (number-like): supports either 0.2 or 20
            - transaction_type (str): "sale" or "purchase"
            - vat_amount (optional number-like): overrides net*rate when provided
        round_to_cents: quantize final payable values to 2 decimals.

    Returns:
        A dict keyed by jurisdiction where value is VAT payable:
        output VAT (sales) - input VAT (purchases).
    """
    totals: dict[str, Decimal] = {}

    for raw in transactions:
        txn = _normalize_transaction(raw)
        vat_amount = _transaction_vat_amount(txn)
        signed_vat = vat_amount if txn.transaction_type == "sale" else -vat_amount
        totals[txn.jurisdiction] = totals.get(txn.jurisdiction, Decimal("0")) + signed_vat

    if round_to_cents:
        return {
            jurisdiction: total.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
            for jurisdiction, total in totals.items()
        }

    return totals
