from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Union

Money = Union[str, int, float, Decimal]
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A VAT-bearing transaction in a given jurisdiction."""

    jurisdiction: str
    amount: Money
    vat_rate: Money | None = None
    vat_amount: Money | None = None
    kind: str = "sale"


def _to_decimal(value: Money) -> Decimal:
    return Decimal(str(value))


def _extract(record: Mapping[str, object] | Transaction) -> tuple[str, Decimal, str]:
    if isinstance(record, Transaction):
        jurisdiction = record.jurisdiction
        kind = record.kind
        amount = _to_decimal(record.amount)
        vat_rate = None if record.vat_rate is None else _to_decimal(record.vat_rate)
        vat_amount = None if record.vat_amount is None else _to_decimal(record.vat_amount)
    else:
        jurisdiction = str(record["jurisdiction"])
        kind = str(record.get("kind", "sale"))
        amount = _to_decimal(record["amount"])  # type: ignore[index]
        vat_rate_raw = record.get("vat_rate")
        vat_amount_raw = record.get("vat_amount")
        vat_rate = None if vat_rate_raw is None else _to_decimal(vat_rate_raw)  # type: ignore[arg-type]
        vat_amount = None if vat_amount_raw is None else _to_decimal(vat_amount_raw)  # type: ignore[arg-type]

    if vat_amount is None and vat_rate is None:
        raise ValueError("Each transaction must include vat_amount or vat_rate.")

    vat = vat_amount if vat_amount is not None else amount * vat_rate  # type: ignore[operator]
    if kind not in {"sale", "purchase"}:
        raise ValueError("Transaction kind must be either 'sale' or 'purchase'.")

    signed_vat = vat if kind == "sale" else -vat
    return jurisdiction, signed_vat, kind


def vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, object] | Transaction],
) -> dict[str, Decimal]:
    """
    Compute net VAT payable per jurisdiction.

    - sale: VAT increases payable amount (output VAT)
    - purchase: VAT reduces payable amount (input VAT)
    """
    totals: dict[str, Decimal] = {}
    for transaction in transactions:
        jurisdiction, signed_vat, _ = _extract(transaction)
        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + signed_vat

    return {
        jurisdiction: amount.quantize(CENT, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in totals.items()
    }
