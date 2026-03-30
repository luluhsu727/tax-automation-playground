from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


VALID_TRANSACTION_TYPES = {"sale", "purchase"}


@dataclass(frozen=True)
class VATTransaction:
    """Normalized transaction used for VAT payable calculations."""

    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "VATTransaction":
        jurisdiction = str(raw.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Transaction must include a non-empty jurisdiction.")

        transaction_type = str(raw.get("transaction_type", "")).strip().lower()
        if transaction_type not in VALID_TRANSACTION_TYPES:
            raise ValueError(
                "transaction_type must be either 'sale' or 'purchase'."
            )

        vat_amount = _extract_vat_amount(raw)
        if vat_amount < Decimal("0"):
            raise ValueError("vat_amount cannot be negative.")

        return cls(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            vat_amount=vat_amount,
        )


@dataclass(frozen=True)
class JurisdictionVATSummary:
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any] | VATTransaction],
    *,
    precision: str = "0.01",
) -> dict[str, JurisdictionVATSummary]:
    """
    Generate net VAT payable per jurisdiction.

    - output_vat: VAT collected from sales.
    - input_vat: VAT paid on purchases.
    - vat_payable: output_vat - input_vat (negative means VAT reclaimable).

    Accepted transaction shapes:
    1) {"jurisdiction", "transaction_type", "vat_amount"}
    2) {"jurisdiction", "transaction_type", "taxable_amount", "vat_rate"}
       - vat_rate can be fractional (0.2 for 20%) or percentage (20 for 20%).
    """
    rounding = Decimal(precision)
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for transaction in transactions:
        normalized = (
            transaction
            if isinstance(transaction, VATTransaction)
            else VATTransaction.from_raw(transaction)
        )

        key = "output_vat" if normalized.transaction_type == "sale" else "input_vat"
        totals[normalized.jurisdiction][key] += normalized.vat_amount

    result: dict[str, JurisdictionVATSummary] = {}
    for jurisdiction in sorted(totals):
        output_vat = _round_currency(totals[jurisdiction]["output_vat"], rounding)
        input_vat = _round_currency(totals[jurisdiction]["input_vat"], rounding)
        vat_payable = _round_currency(output_vat - input_vat, rounding)
        result[jurisdiction] = JurisdictionVATSummary(
            output_vat=output_vat,
            input_vat=input_vat,
            vat_payable=vat_payable,
        )

    return result


def _extract_vat_amount(raw: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in raw:
        return _to_decimal(raw["vat_amount"], field="vat_amount")

    taxable_amount = _to_decimal(raw.get("taxable_amount"), field="taxable_amount")
    vat_rate = _to_decimal(raw.get("vat_rate"), field="vat_rate")
    if vat_rate > Decimal("1"):
        vat_rate = vat_rate / Decimal("100")

    return taxable_amount * vat_rate


def _to_decimal(value: Any, *, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid numeric value for {field}.") from None


def _round_currency(amount: Decimal, precision: Decimal) -> Decimal:
    return amount.quantize(precision, rounding=ROUND_HALF_UP)
