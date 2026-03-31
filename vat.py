"""Utilities for generating VAT payable per jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Convert any numeric-like value into Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_currency(value: Decimal, precision: Decimal = TWOPLACES) -> Decimal:
    return value.quantize(precision, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class VATEntry:
    """Single VAT movement in a jurisdiction.

    output_vat:
        VAT collected on sales.
    input_vat:
        VAT paid on purchases that can be deducted.
    """

    jurisdiction: str
    output_vat: Decimal | int | float | str = Decimal("0")
    input_vat: Decimal | int | float | str = Decimal("0")


@dataclass(frozen=True)
class VATResult:
    """Computed VAT totals for a jurisdiction."""

    jurisdiction: str
    total_output_vat: Decimal
    total_input_vat: Decimal
    net_vat: Decimal
    vat_payable: Decimal
    vat_credit_carry_forward: Decimal


def generate_vat_payable_by_jurisdiction(
    entries: Iterable[VATEntry],
    *,
    currency_precision: Decimal | str = TWOPLACES,
) -> dict[str, VATResult]:
    """Generate VAT payable for each jurisdiction.

    Net VAT = total_output_vat - total_input_vat
    VAT payable = max(Net VAT, 0)
    VAT credit carry-forward = max(-Net VAT, 0)
    """

    precision = (
        currency_precision
        if isinstance(currency_precision, Decimal)
        else Decimal(str(currency_precision))
    )

    totals: dict[str, tuple[Decimal, Decimal]] = {}

    for entry in entries:
        output_vat = _to_decimal(entry.output_vat)
        input_vat = _to_decimal(entry.input_vat)

        current_output, current_input = totals.get(
            entry.jurisdiction, (Decimal("0"), Decimal("0"))
        )
        totals[entry.jurisdiction] = (
            current_output + output_vat,
            current_input + input_vat,
        )

    results: dict[str, VATResult] = {}
    for jurisdiction, (total_output_vat, total_input_vat) in totals.items():
        net_vat = total_output_vat - total_input_vat
        vat_payable = max(net_vat, Decimal("0"))
        vat_credit = max(-net_vat, Decimal("0"))

        results[jurisdiction] = VATResult(
            jurisdiction=jurisdiction,
            total_output_vat=_quantize_currency(total_output_vat, precision),
            total_input_vat=_quantize_currency(total_input_vat, precision),
            net_vat=_quantize_currency(net_vat, precision),
            vat_payable=_quantize_currency(vat_payable, precision),
            vat_credit_carry_forward=_quantize_currency(vat_credit, precision),
        )

    return results
