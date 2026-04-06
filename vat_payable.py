"""Utilities for generating VAT payable per jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, MutableMapping


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A taxable transaction used for VAT calculations.

    Attributes:
        jurisdiction: Tax jurisdiction (for example, "UK" or "DE").
        amount: Net transaction amount (VAT-exclusive).
        transaction_type: Either "sale" (output VAT) or "purchase" (input VAT).
        vat_rate: Optional VAT rate as a decimal fraction, e.g. 0.2 for 20%.
    """

    jurisdiction: str
    amount: Decimal
    transaction_type: str
    vat_rate: Decimal | None = None


@dataclass(frozen=True)
class JurisdictionVATSummary:
    """VAT totals for one jurisdiction."""

    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _get_rate(
    transaction: Transaction, jurisdiction_vat_rates: Mapping[str, Decimal]
) -> Decimal:
    if transaction.vat_rate is not None:
        rate = transaction.vat_rate
    else:
        if transaction.jurisdiction not in jurisdiction_vat_rates:
            raise ValueError(
                f"Missing VAT rate for jurisdiction '{transaction.jurisdiction}'. "
                "Provide transaction.vat_rate or jurisdiction_vat_rates entry."
            )
        rate = jurisdiction_vat_rates[transaction.jurisdiction]

    if rate < 0:
        raise ValueError("VAT rate cannot be negative.")
    return rate


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
    jurisdiction_vat_rates: Mapping[str, Decimal | int | float | str] | None = None,
) -> dict[str, JurisdictionVATSummary]:
    """Generate VAT payable totals for each jurisdiction.

    VAT payable is calculated as output VAT (from sales) minus input VAT
    (from purchases), per jurisdiction.
    """

    rates: dict[str, Decimal] = {
        key: _to_decimal(value)
        for key, value in (jurisdiction_vat_rates or {}).items()
    }

    totals: MutableMapping[str, dict[str, Decimal]] = {}
    for tx in transactions:
        if tx.amount < 0:
            raise ValueError("Transaction amount cannot be negative.")
        if tx.transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                "transaction_type must be either 'sale' or 'purchase'."
            )

        rate = _get_rate(tx, rates)
        vat_amount = _quantize(tx.amount * rate)

        jurisdiction_totals = totals.setdefault(
            tx.jurisdiction,
            {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")},
        )

        if tx.transaction_type == "sale":
            jurisdiction_totals["output_vat"] += vat_amount
        else:
            jurisdiction_totals["input_vat"] += vat_amount

    return {
        jurisdiction: JurisdictionVATSummary(
            output_vat=_quantize(values["output_vat"]),
            input_vat=_quantize(values["input_vat"]),
            vat_payable=_quantize(values["output_vat"] - values["input_vat"]),
        )
        for jurisdiction, values in totals.items()
    }
