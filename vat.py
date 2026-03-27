"""VAT calculation helpers for jurisdiction-level reporting."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from vat_core import money, normalize_jurisdiction, normalize_tx_type, to_decimal, to_rate


class Transaction:
    """Single taxable transaction supporting multiple historical shapes.

    Supported constructor forms:
      1) Transaction("DE", "sale", Decimal("100"), Decimal("0.19"))
      2) Transaction("DE", Decimal("100"), Decimal("0.19"), "sale")
      3) keyword form with transaction_type/net_amount/vat_rate or kind/amount/vat_rate
    """

    def __init__(self, jurisdiction: str, *args, **kwargs) -> None:
        self.jurisdiction = normalize_jurisdiction(jurisdiction)

        if kwargs:
            self._from_kwargs(kwargs)
            return

        if len(args) != 3:
            raise ValueError("Transaction requires three positional fields after jurisdiction")

        first, second, third = args
        if isinstance(first, str):
            # (transaction_type, net_amount, vat_rate)
            self.transaction_type = normalize_tx_type(first)
            self.net_amount = to_decimal(second, field_name="net_amount")
            self.vat_rate = to_rate(third, field_name="vat_rate")
        else:
            # (amount, vat_rate, kind)
            self.net_amount = to_decimal(first, field_name="amount")
            self.vat_rate = to_rate(second, field_name="vat_rate")
            self.transaction_type = normalize_tx_type(third)

        self.kind = self.transaction_type
        self.amount = self.net_amount

    @classmethod
    def build(
        cls,
        jurisdiction: str,
        transaction_type: str,
        net_amount: str | int | float | Decimal,
        vat_rate: str | int | float | Decimal,
    ) -> "Transaction":
        return cls(jurisdiction, transaction_type, net_amount, vat_rate)

    def _from_kwargs(self, raw: dict) -> None:
        tx_type = raw.get("transaction_type", raw.get("kind"))
        amount_value = raw.get("net_amount", raw.get("amount"))
        if tx_type is None or amount_value is None or raw.get("vat_rate") is None:
            raise ValueError(
                "Expected transaction_type/kind, net_amount/amount, and vat_rate in keyword input"
            )
        self.transaction_type = normalize_tx_type(tx_type)
        self.net_amount = to_decimal(amount_value, field_name="net_amount")
        self.vat_rate = to_rate(raw.get("vat_rate"), field_name="vat_rate")
        self.kind = self.transaction_type
        self.amount = self.net_amount

    def vat_amount(self) -> Decimal:
        return money(self.net_amount * self.vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Generate net VAT payable for each jurisdiction."""
    vat_payable: dict[str, Decimal] = {}

    for tx in transactions:
        signed_vat = tx.vat_amount() if tx.transaction_type == "sale" else -tx.vat_amount()
        vat_payable[tx.jurisdiction] = vat_payable.get(tx.jurisdiction, Decimal("0")) + signed_vat

    return {j: money(v) for j, v in sorted(vat_payable.items())}


def vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction | dict],
) -> dict[str, dict[str, Decimal]]:
    """Return output/input/payable/credit VAT totals per jurisdiction."""
    result: dict[str, dict[str, Decimal]] = {}

    for raw_tx in transactions:
        tx = raw_tx if isinstance(raw_tx, Transaction) else Transaction(**raw_tx)
        stats = result.setdefault(
            tx.jurisdiction,
            {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
                "vat_payable": Decimal("0.00"),
                "vat_credit": Decimal("0.00"),
            },
        )
        if tx.transaction_type == "sale":
            stats["output_vat"] = money(stats["output_vat"] + tx.vat_amount())
        else:
            stats["input_vat"] = money(stats["input_vat"] + tx.vat_amount())

    for values in result.values():
        net = money(values["output_vat"] - values["input_vat"])
        values["vat_payable"] = net
        values["vat_credit"] = money(-net) if net < 0 else Decimal("0.00")

    return result


__all__ = ["Transaction", "generate_vat_payable_by_jurisdiction", "vat_to_be_paid_by_jurisdiction"]

