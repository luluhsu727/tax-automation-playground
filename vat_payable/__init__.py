"""Public API for VAT payable calculations.

This package-level API keeps compatibility with earlier challenge revisions
that imported symbols directly from ``vat_payable``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from vat_core import VatError, money, normalize_jurisdiction, normalize_tx_type, to_decimal, to_rate


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction in normalized shape."""

    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal


def transaction_from_record(record: dict[str, object]) -> Transaction:
    """Create a Transaction from either explicit or derived VAT fields."""
    jurisdiction = normalize_jurisdiction(record.get("jurisdiction"))
    tx_type = normalize_tx_type(record.get("transaction_type", record.get("type")))

    if "vat_amount" in record:
        vat_amount = to_decimal(record.get("vat_amount"), field_name="vat_amount")
    else:
        if "net_amount" in record:
            amount_value = record.get("net_amount")
            amount_field = "net_amount"
        else:
            amount_value = record.get("amount")
            amount_field = "amount"
        if amount_value is None or record.get("vat_rate") is None:
            raise ValueError(
                "Record must contain either 'vat_amount' or both "
                "'net_amount/amount' and 'vat_rate'"
            )
        net_amount = to_decimal(amount_value, field_name=amount_field)
        vat_rate = to_rate(record.get("vat_rate"), field_name="vat_rate")
        vat_amount = net_amount * vat_rate

    if vat_amount < 0:
        raise ValueError("VAT amount cannot be negative")

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=tx_type,
        vat_amount=money(vat_amount),
    )


def load_transactions(path: str | Path) -> list[Transaction]:
    file_path = Path(path)
    records = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Input JSON must be an array of transaction records")
    return [transaction_from_record(record) for record in records]


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Return net VAT payable per jurisdiction."""
    totals: dict[str, Decimal] = {}
    for transaction in transactions:
        current_total = totals.get(transaction.jurisdiction, Decimal("0"))
        if transaction.transaction_type == "sale":
            current_total += transaction.vat_amount
        elif transaction.transaction_type == "purchase":
            current_total -= transaction.vat_amount
        else:
            raise ValueError(f"Unknown transaction type: {transaction.transaction_type}")
        totals[transaction.jurisdiction] = current_total

    normalized: dict[str, Decimal] = {}
    for jurisdiction, total in sorted(totals.items()):
        if floor_at_zero and total < 0:
            total = Decimal("0")
        normalized[jurisdiction] = money(total)
    return normalized


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Backward-compatible alias used by older task variants."""
    return calculate_vat_payable_by_jurisdiction(
        transactions, floor_at_zero=floor_at_zero
    )


def _format_report(vat_by_jurisdiction: dict[str, Decimal]) -> str:
    if not vat_by_jurisdiction:
        return "No transactions."
    lines = []
    for jurisdiction in sorted(vat_by_jurisdiction):
        lines.append(f"{jurisdiction}: {vat_by_jurisdiction[jurisdiction]:.2f}")
    return "\n".join(lines)


__all__ = [
    "Transaction",
    "calculate_vat_payable_by_jurisdiction",
    "generate_vat_payable_by_jurisdiction",
    "load_transactions",
    "transaction_from_record",
    "_format_report",
    "VatError",
]
