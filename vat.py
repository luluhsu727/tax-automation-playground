"""VAT payable computation by jurisdiction.

Given a list of transactions with jurisdiction, amount, and VAT rate,
this module computes output VAT, input VAT, and net VAT payable for each
jurisdiction.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A taxable transaction.

    Attributes:
        jurisdiction: Tax jurisdiction code/name (e.g., "DE", "FR").
        amount: Net amount before VAT.
        vat_rate: VAT rate as decimal percentage (e.g., 0.20 for 20%).
        kind: "sale" for output VAT or "purchase" for input VAT.
    """

    jurisdiction: str
    amount: Decimal
    vat_rate: Decimal
    kind: str


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_kind(kind: str) -> str:
    normalized = kind.strip().lower()
    if normalized not in {"sale", "purchase"}:
        raise ValueError(f"Unsupported transaction kind: {kind!r}")
    return normalized


def vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction | dict],
) -> dict[str, dict[str, Decimal]]:
    """Calculate VAT amounts grouped by jurisdiction.

    Returns a mapping:
        {
          "<jurisdiction>": {
            "output_vat": Decimal,
            "input_vat": Decimal,
            "vat_payable": Decimal,  # output - input
            "vat_credit": Decimal,   # positive when vat_payable < 0, else 0
          }
        }
    """

    result: dict[str, dict[str, Decimal]] = {}

    for raw_tx in transactions:
        if isinstance(raw_tx, Transaction):
            tx = raw_tx
        else:
            tx = Transaction(
                jurisdiction=str(raw_tx["jurisdiction"]),
                amount=_to_decimal(raw_tx["amount"]),
                vat_rate=_to_decimal(raw_tx["vat_rate"]),
                kind=str(raw_tx["kind"]),
            )

        jurisdiction = tx.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("Jurisdiction cannot be empty")

        kind = _normalize_kind(tx.kind)
        amount = _to_decimal(tx.amount)
        vat_rate = _to_decimal(tx.vat_rate)

        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if vat_rate < 0:
            raise ValueError("VAT rate cannot be negative")

        vat_amount = _q(amount * vat_rate)

        if jurisdiction not in result:
            result[jurisdiction] = {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
                "vat_payable": Decimal("0.00"),
                "vat_credit": Decimal("0.00"),
            }

        if kind == "sale":
            result[jurisdiction]["output_vat"] = _q(
                result[jurisdiction]["output_vat"] + vat_amount
            )
        else:
            result[jurisdiction]["input_vat"] = _q(
                result[jurisdiction]["input_vat"] + vat_amount
            )

    for jurisdiction, values in result.items():
        net = _q(values["output_vat"] - values["input_vat"])
        values["vat_payable"] = net
        values["vat_credit"] = _q(-net) if net < 0 else Decimal("0.00")

    return result
