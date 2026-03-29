"""VAT calculation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Convert input to Decimal without float precision artifacts."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_currency(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    """One taxable transaction."""

    jurisdiction: str
    net_amount: Decimal
    vat_rate: Decimal
    transaction_type: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "Transaction":
        """Build a transaction from a dictionary-like object."""
        return cls(
            jurisdiction=str(payload["jurisdiction"]),
            net_amount=_to_decimal(payload["net_amount"]),
            vat_rate=_to_decimal(payload["vat_rate"]),
            transaction_type=str(payload["transaction_type"]),
        )

    def vat_amount(self) -> Decimal:
        """VAT amount for this transaction rounded to cents."""
        return _round_currency(self.net_amount * self.vat_rate)

    def validate(self) -> None:
        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction must not be empty")
        if self.net_amount < 0:
            raise ValueError("net_amount must be >= 0")
        if self.vat_rate < 0:
            raise ValueError("vat_rate must be >= 0")
        if self.transaction_type not in {"sale", "purchase"}:
            raise ValueError("transaction_type must be either 'sale' or 'purchase'")


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Aggregated VAT values for one jurisdiction."""

    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    vat_payable: Decimal
    vat_credit: Decimal


def _normalize_transaction(item: Transaction | Mapping[str, object]) -> Transaction:
    if isinstance(item, Transaction):
        tx = item
    elif isinstance(item, Mapping):
        tx = Transaction.from_mapping(item)
    else:
        raise TypeError("items must be Transaction or mapping")

    tx.validate()
    return tx


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, JurisdictionVatSummary]:
    """
    Aggregate VAT by jurisdiction and compute amount payable.

    Sales create output VAT. Purchases create input VAT.
    Net VAT = output VAT - input VAT.
    - If positive: payable.
    - If negative: credit.
    """
    buckets: dict[str, dict[str, Decimal]] = {}

    for raw_item in transactions:
        tx = _normalize_transaction(raw_item)
        vat = tx.vat_amount()
        if tx.jurisdiction not in buckets:
            buckets[tx.jurisdiction] = {
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
            }

        target = buckets[tx.jurisdiction]
        if tx.transaction_type == "sale":
            target["output_vat"] += vat
        else:
            target["input_vat"] += vat

    results: dict[str, JurisdictionVatSummary] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _round_currency(buckets[jurisdiction]["output_vat"])
        input_vat = _round_currency(buckets[jurisdiction]["input_vat"])
        net_vat = _round_currency(output_vat - input_vat)
        vat_payable = net_vat if net_vat > 0 else Decimal("0.00")
        vat_credit = -net_vat if net_vat < 0 else Decimal("0.00")
        results[jurisdiction] = JurisdictionVatSummary(
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            vat_payable=_round_currency(vat_payable),
            vat_credit=_round_currency(vat_credit),
        )

    return results
