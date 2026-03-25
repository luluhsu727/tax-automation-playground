"""Utilities to generate VAT payable by jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class VATTransaction:
    """Represents an input line for VAT payable calculation."""

    jurisdiction: str
    vat_amount: Decimal


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"Field '{field_name}' is required.")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive.
        raise ValueError(f"Field '{field_name}' must be numeric.") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Accept VAT rate as fraction (0.20) or percentage (20)."""
    if rate > Decimal("1"):
        return rate / Decimal("100")
    return rate


def _extract_transaction(
    row: Mapping[str, Any],
    jurisdiction_key: str,
    net_amount_key: str,
    vat_rate_key: str,
    vat_amount_key: str,
) -> VATTransaction:
    jurisdiction = row.get(jurisdiction_key)
    if not jurisdiction:
        raise ValueError(f"Field '{jurisdiction_key}' is required and cannot be empty.")

    if row.get(vat_amount_key) is not None:
        vat_amount = _to_decimal(row.get(vat_amount_key), vat_amount_key)
    else:
        net_amount = _to_decimal(row.get(net_amount_key), net_amount_key)
        vat_rate = _to_decimal(row.get(vat_rate_key), vat_rate_key)
        vat_amount = net_amount * _normalize_rate(vat_rate)

    return VATTransaction(jurisdiction=str(jurisdiction), vat_amount=vat_amount)


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    jurisdiction_key: str = "jurisdiction",
    net_amount_key: str = "net_amount",
    vat_rate_key: str = "vat_rate",
    vat_amount_key: str = "vat_amount",
    rounding: str | Decimal = TWOPLACES,
) -> dict[str, Decimal]:
    """Generate total VAT payable grouped by jurisdiction.

    Input rows can provide:
    - direct `vat_amount`, or
    - `net_amount` and `vat_rate` (where rate can be 0.2 or 20).
    """
    rounding_quantizer = Decimal(str(rounding))
    totals: dict[str, Decimal] = {}

    for row in transactions:
        tx = _extract_transaction(
            row=row,
            jurisdiction_key=jurisdiction_key,
            net_amount_key=net_amount_key,
            vat_rate_key=vat_rate_key,
            vat_amount_key=vat_amount_key,
        )
        totals[tx.jurisdiction] = totals.get(tx.jurisdiction, Decimal("0")) + tx.vat_amount

    return {
        jurisdiction: amount.quantize(rounding_quantizer, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in sorted(totals.items())
    }
