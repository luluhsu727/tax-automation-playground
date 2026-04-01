"""VAT payable calculations grouped by jurisdiction.

VAT payable is calculated as:
    output VAT (from sales) - input VAT (from purchases)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """VAT totals for a single jurisdiction."""

    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _resolve_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return _money(_to_decimal(transaction["vat_amount"], field_name="vat_amount"))

    if "net_amount" not in transaction:
        raise ValueError("Transaction must include 'net_amount' when 'vat_amount' is absent")
    if "vat_rate" not in transaction:
        raise ValueError("Transaction must include 'vat_rate' when 'vat_amount' is absent")

    net_amount = _to_decimal(transaction["net_amount"], field_name="net_amount")
    vat_rate = _to_decimal(transaction["vat_rate"], field_name="vat_rate")
    return _money(net_amount * vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    clamp_negative_payable: bool = False,
) -> dict[str, JurisdictionVatSummary]:
    """Generate VAT payable per jurisdiction.

    Expected transaction keys:
      - jurisdiction: str
      - transaction_type: "sale" or "purchase"
      - vat_amount: optional explicit VAT amount
      - net_amount + vat_rate: required when vat_amount is omitted
    """

    output_by_jurisdiction: dict[str, Decimal] = {}
    input_by_jurisdiction: dict[str, Decimal] = {}

    for idx, transaction in enumerate(transactions):
        if "jurisdiction" not in transaction or not transaction["jurisdiction"]:
            raise ValueError(f"Transaction #{idx} is missing 'jurisdiction'")
        if "transaction_type" not in transaction:
            raise ValueError(f"Transaction #{idx} is missing 'transaction_type'")

        jurisdiction = str(transaction["jurisdiction"]).strip()
        transaction_type = str(transaction["transaction_type"]).strip().lower()
        vat_amount = _resolve_vat_amount(transaction)

        if transaction_type == "sale":
            output_by_jurisdiction[jurisdiction] = output_by_jurisdiction.get(
                jurisdiction, Decimal("0.00")
            ) + vat_amount
            input_by_jurisdiction.setdefault(jurisdiction, Decimal("0.00"))
        elif transaction_type == "purchase":
            input_by_jurisdiction[jurisdiction] = input_by_jurisdiction.get(
                jurisdiction, Decimal("0.00")
            ) + vat_amount
            output_by_jurisdiction.setdefault(jurisdiction, Decimal("0.00"))
        else:
            raise ValueError(
                f"Transaction #{idx} has invalid transaction_type {transaction_type!r}; "
                "expected 'sale' or 'purchase'"
            )

    all_jurisdictions = set(output_by_jurisdiction) | set(input_by_jurisdiction)
    results: dict[str, JurisdictionVatSummary] = {}

    for jurisdiction in sorted(all_jurisdictions):
        output_vat = _money(output_by_jurisdiction.get(jurisdiction, Decimal("0.00")))
        input_vat = _money(input_by_jurisdiction.get(jurisdiction, Decimal("0.00")))
        payable = output_vat - input_vat
        if clamp_negative_payable and payable < 0:
            payable = Decimal("0.00")

        results[jurisdiction] = JurisdictionVatSummary(
            output_vat=output_vat,
            input_vat=input_vat,
            vat_payable=_money(payable),
        )

    return results
