from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Literal


TransactionKind = Literal["sale", "purchase"]


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction.

    Attributes:
        jurisdiction: Tax jurisdiction code/name (for example: "DE", "FR", "UK").
        taxable_amount: Net amount before VAT.
        vat_rate: VAT rate as percentage or fraction.
            - 20 means 20%
            - 0.2 means 20%
        kind:
            - "sale" -> output VAT (increases payable VAT)
            - "purchase" -> input VAT (decreases payable VAT)
    """

    jurisdiction: str
    taxable_amount: Decimal
    vat_rate: Decimal
    kind: TransactionKind


def _to_rate_fraction(rate: Decimal) -> Decimal:
    """Normalize a VAT rate to a fraction in [0, 1+] space."""

    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    return rate / Decimal("100") if rate > 1 else rate


def _quantize_money(value: Decimal) -> Decimal:
    """Round to currency precision (2 dp) using half-up."""

    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Return net VAT payable per jurisdiction.

    Net VAT payable formula per jurisdiction:
        total_output_vat_on_sales - total_input_vat_on_purchases

    Positive values mean VAT to pay.
    Negative values mean recoverable VAT/refund position.
    """

    output_vat_by_jurisdiction: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    input_vat_by_jurisdiction: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for txn in transactions:
        rate_fraction = _to_rate_fraction(txn.vat_rate)
        vat_amount = _quantize_money(txn.taxable_amount * rate_fraction)

        if txn.kind == "sale":
            output_vat_by_jurisdiction[txn.jurisdiction] += vat_amount
        elif txn.kind == "purchase":
            input_vat_by_jurisdiction[txn.jurisdiction] += vat_amount
        else:
            raise ValueError(f"Unsupported transaction kind: {txn.kind}")

    all_jurisdictions = set(output_vat_by_jurisdiction) | set(input_vat_by_jurisdiction)
    net_by_jurisdiction: dict[str, Decimal] = {}
    for jurisdiction in sorted(all_jurisdictions):
        net_by_jurisdiction[jurisdiction] = _quantize_money(
            output_vat_by_jurisdiction[jurisdiction] - input_vat_by_jurisdiction[jurisdiction]
        )

    return net_by_jurisdiction
