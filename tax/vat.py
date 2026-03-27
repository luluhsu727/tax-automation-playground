from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List

TWOPLACES = Decimal("0.01")


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal

    @property
    def vat_amount(self) -> Decimal:
        return _to_money(self.net_amount * self.vat_rate)


@dataclass(frozen=True)
class JurisdictionVatSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> List[JurisdictionVatSummary]:
    """
    Compute VAT payable for each jurisdiction.

    Rules:
      - sale contributes to output VAT
      - purchase contributes to input VAT
      - VAT payable = output VAT - input VAT
    """
    buckets: Dict[str, Dict[str, Decimal]] = {}

    for tx in transactions:
        tx_type = tx.transaction_type.strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type '{tx.transaction_type}'. "
                "Expected 'sale' or 'purchase'."
            )

        jurisdiction = tx.jurisdiction.strip().upper()
        if not jurisdiction:
            raise ValueError("Jurisdiction cannot be empty.")

        if jurisdiction not in buckets:
            buckets[jurisdiction] = {"output_vat": Decimal("0"), "input_vat": Decimal("0")}

        if tx_type == "sale":
            buckets[jurisdiction]["output_vat"] += tx.vat_amount
        else:
            buckets[jurisdiction]["input_vat"] += tx.vat_amount

    summaries: List[JurisdictionVatSummary] = []
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
        vat_payable = _to_money(output_vat - input_vat)
        summaries.append(
            JurisdictionVatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                vat_payable=vat_payable,
            )
        )

    return summaries
