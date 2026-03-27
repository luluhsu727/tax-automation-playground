from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List

from vat_core import money, normalize_jurisdiction, normalize_tx_type, to_decimal, to_rate


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal

    def __init__(self, jurisdiction: str, transaction_type: str, net_amount, vat_rate) -> None:
        object.__setattr__(self, "jurisdiction", normalize_jurisdiction(jurisdiction))
        object.__setattr__(self, "transaction_type", normalize_tx_type(transaction_type))
        object.__setattr__(self, "net_amount", to_decimal(net_amount, field_name="net_amount"))
        object.__setattr__(self, "vat_rate", to_rate(vat_rate, field_name="vat_rate"))

    @property
    def vat_amount(self) -> Decimal:
        return money(self.net_amount * self.vat_rate)


@dataclass(frozen=True)
class JurisdictionVatSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> List[JurisdictionVatSummary]:
    """Compute output/input VAT and payable amounts grouped by jurisdiction."""
    buckets: Dict[str, Dict[str, Decimal]] = {}

    for tx in transactions:
        if tx.jurisdiction not in buckets:
            buckets[tx.jurisdiction] = {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}

        if tx.transaction_type == "sale":
            buckets[tx.jurisdiction]["output_vat"] += tx.vat_amount
        else:
            buckets[tx.jurisdiction]["input_vat"] += tx.vat_amount

    summaries: List[JurisdictionVatSummary] = []
    for jurisdiction in sorted(buckets):
        output_vat = money(buckets[jurisdiction]["output_vat"])
        input_vat = money(buckets[jurisdiction]["input_vat"])
        vat_payable = money(output_vat - input_vat)
        summaries.append(
            JurisdictionVatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                vat_payable=vat_payable,
            )
        )

    return summaries
