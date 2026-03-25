"""Utilities to compute VAT payable per jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: object) -> Decimal:
    """Normalize numeric inputs to Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    """Round money using common accounting half-up precision."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class VatBreakdown:
    """Computed VAT figures for one jurisdiction."""

    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    payable_vat: Decimal
    refundable_vat: Decimal


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, VatBreakdown]:
    """
    Compute VAT position for every jurisdiction from transaction entries.

    Expected transaction keys:
      - jurisdiction (str)
      - amount (number-like): net taxable amount
      - vat_rate (number-like): VAT rate such as 0.20 for 20%
      - kind (str): "sale" for output VAT, "purchase" for input VAT

    Returns:
      A mapping of jurisdiction -> VatBreakdown.
    """
    totals: dict[str, dict[str, Decimal]] = {}

    for idx, tx in enumerate(transactions, start=1):
        jurisdiction = tx.get("jurisdiction")
        kind = tx.get("kind")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(f"Transaction {idx} has invalid jurisdiction")
        if kind not in {"sale", "purchase"}:
            raise ValueError(f"Transaction {idx} has invalid kind '{kind}'")

        try:
            amount = _to_decimal(tx.get("amount"))
            vat_rate = _to_decimal(tx.get("vat_rate"))
        except Exception as exc:  # pragma: no cover - defensive conversion guard
            raise ValueError(f"Transaction {idx} has invalid numeric values") from exc

        vat = _round_money(amount * vat_rate)
        bucket = totals.setdefault(
            jurisdiction,
            {"output_vat": Decimal("0"), "input_vat": Decimal("0")},
        )
        if kind == "sale":
            bucket["output_vat"] += vat
        else:
            bucket["input_vat"] += vat

    result: dict[str, VatBreakdown] = {}
    for jurisdiction, values in totals.items():
        output_vat = _round_money(values["output_vat"])
        input_vat = _round_money(values["input_vat"])
        net_vat = _round_money(output_vat - input_vat)
        payable_vat = net_vat if net_vat > 0 else Decimal("0.00")
        refundable_vat = -net_vat if net_vat < 0 else Decimal("0.00")
        result[jurisdiction] = VatBreakdown(
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            payable_vat=payable_vat,
            refundable_vat=refundable_vat,
        )

    return result


def vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, Decimal]:
    """
    Return only positive VAT payable totals by jurisdiction.

    Jurisdictions with a net refund position are returned with 0.00 payable.
    """
    breakdown = calculate_vat_payable_by_jurisdiction(transactions)
    return {name: values.payable_vat for name, values in breakdown.items()}

