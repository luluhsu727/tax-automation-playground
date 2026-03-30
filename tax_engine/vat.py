"""VAT payable calculation utilities."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

TWOPLACES = Decimal("0.01")

SALE_TYPES = {"sale", "sales", "output", "output_vat"}
PURCHASE_TYPES = {"purchase", "purchases", "input", "input_vat", "expense"}


def _to_decimal(value: Decimal | str | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_transaction_type(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction entry."""

    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal | None = None
    vat_amount: Decimal | None = None

    def resolved_vat_amount(self) -> Decimal:
        """Return VAT amount, deriving from net_amount and vat_rate when needed."""
        if self.vat_amount is not None:
            return _to_decimal(self.vat_amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        if self.vat_rate is None:
            raise ValueError(
                "Transaction must include vat_amount or vat_rate: "
                f"{self.jurisdiction} / {self.transaction_type}"
            )

        vat = _to_decimal(self.net_amount) * _to_decimal(self.vat_rate)
        return vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    def direction(self) -> int:
        """+1 for output VAT, -1 for input VAT."""
        normalized_type = _normalize_transaction_type(self.transaction_type)
        if normalized_type in SALE_TYPES:
            return 1
        if normalized_type in PURCHASE_TYPES:
            return -1
        raise ValueError(
            f"Unknown transaction_type '{self.transaction_type}'. "
            "Use sale/output for output VAT or purchase/input for input VAT."
        )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """
    Calculate VAT payable per jurisdiction.

    VAT payable = output VAT - input VAT.
    Positive values indicate VAT due; negative values indicate a reclaim/refund position.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for transaction in transactions:
        jurisdiction = transaction.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("Transaction jurisdiction cannot be empty.")

        vat_amount = transaction.resolved_vat_amount()
        totals[jurisdiction] += Decimal(transaction.direction()) * vat_amount

    return {
        jurisdiction: amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in sorted(totals.items())
    }
