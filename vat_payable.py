"""Utilities to generate VAT payable amounts by jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

TWO_DECIMALS = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Convert numbers/strings to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class VATTransaction:
    """Single transaction used to derive jurisdiction VAT totals."""

    jurisdiction: str
    amount: Decimal
    vat_rate: Decimal
    transaction_type: str
    vat_amount: Decimal | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "VATTransaction":
        return cls(
            jurisdiction=str(payload["jurisdiction"]),
            amount=_to_decimal(payload["amount"]),
            vat_rate=_to_decimal(payload["vat_rate"]),
            transaction_type=str(payload["transaction_type"]).lower(),
            vat_amount=(
                _to_decimal(payload["vat_amount"])
                if payload.get("vat_amount") is not None
                else None
            ),
        )


def _normalize_transaction(item: VATTransaction | Mapping[str, Any]) -> VATTransaction:
    transaction = item if isinstance(item, VATTransaction) else VATTransaction.from_mapping(item)

    if not transaction.jurisdiction.strip():
        raise ValueError("jurisdiction must be a non-empty string")
    if transaction.amount < 0:
        raise ValueError("amount cannot be negative")
    if transaction.vat_rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if transaction.vat_amount is not None and transaction.vat_amount < 0:
        raise ValueError("vat_amount cannot be negative")
    if transaction.transaction_type not in {"sale", "purchase"}:
        raise ValueError("transaction_type must be either 'sale' or 'purchase'")

    return transaction


def _vat_value(transaction: VATTransaction) -> Decimal:
    if transaction.vat_amount is not None:
        return _quantize(transaction.vat_amount)
    return _quantize(transaction.amount * transaction.vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[VATTransaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Generate VAT totals grouped by jurisdiction.

    Returns a dictionary keyed by jurisdiction with:
      - output_vat: VAT collected on sales
      - input_vat: VAT paid on purchases
      - net_vat: output_vat - input_vat
      - vat_payable: max(net_vat, 0)
      - vat_refundable: max(-net_vat, 0)
    """

    totals: dict[str, dict[str, Decimal]] = {}

    for raw in transactions:
        tx = _normalize_transaction(raw)
        vat = _vat_value(tx)

        if tx.jurisdiction not in totals:
            totals[tx.jurisdiction] = {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
            }

        if tx.transaction_type == "sale":
            totals[tx.jurisdiction]["output_vat"] += vat
        else:
            totals[tx.jurisdiction]["input_vat"] += vat

    for jurisdiction, figures in totals.items():
        output_vat = _quantize(figures["output_vat"])
        input_vat = _quantize(figures["input_vat"])
        net_vat = _quantize(output_vat - input_vat)
        totals[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": max(net_vat, Decimal("0.00")),
            "vat_refundable": max(-net_vat, Decimal("0.00")),
        }

    return totals
