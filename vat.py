"""VAT calculation helpers for jurisdiction-level reporting."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Literal

CENT = Decimal("0.01")


def _to_decimal(value: str | int | float | Decimal) -> Decimal:
    """Convert numeric-like values into Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class Transaction:
    """Single taxable transaction.

    - "sale" increases VAT payable (output VAT).
    - "purchase" decreases VAT payable (input VAT credit).
    """

    jurisdiction: str
    transaction_type: Literal["sale", "purchase"]
    net_amount: Decimal
    vat_rate: Decimal

    @classmethod
    def build(
        cls,
        jurisdiction: str,
        transaction_type: Literal["sale", "purchase"],
        net_amount: str | int | float | Decimal,
        vat_rate: str | int | float | Decimal,
    ) -> "Transaction":
        """Factory accepting common numeric input types."""
        return cls(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            net_amount=_to_decimal(net_amount),
            vat_rate=_to_decimal(vat_rate),
        )

    def vat_amount(self) -> Decimal:
        """VAT amount rounded to cents using half-up."""
        return (self.net_amount * self.vat_rate).quantize(CENT, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Generate net VAT payable for each jurisdiction.

    Net VAT payable = output VAT from sales - input VAT from purchases.
    A negative value means a recoverable VAT credit for that jurisdiction.
    """
    vat_payable: dict[str, Decimal] = {}

    for tx in transactions:
        if tx.transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type '{tx.transaction_type}' "
                "(expected 'sale' or 'purchase')."
            )

        signed_vat = tx.vat_amount() if tx.transaction_type == "sale" else -tx.vat_amount()
        vat_payable[tx.jurisdiction] = vat_payable.get(tx.jurisdiction, Decimal("0")) + signed_vat

    for jurisdiction, amount in vat_payable.items():
        vat_payable[jurisdiction] = amount.quantize(CENT, rounding=ROUND_HALF_UP)

    return dict(sorted(vat_payable.items()))
