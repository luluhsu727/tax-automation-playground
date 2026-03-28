"""VAT payable calculation helpers.

This module provides functions to generate VAT to be paid for each jurisdiction.
It supports transaction records with either:
  - explicit ``vat_amount``, or
  - ``amount``/``net_amount`` and ``vat_rate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Literal


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert ``value`` to Decimal and raise a clear ValueError on failure."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {value!r}") from exc


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_rate(raw_rate: Any) -> Decimal:
    """Accept VAT rate as fraction (0.2) or percent (20)."""
    rate = _to_decimal(raw_rate, "vat_rate")
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


@dataclass(frozen=True)
class Transaction:
    """Single VAT-relevant transaction."""

    jurisdiction: str
    transaction_type: Literal["sale", "purchase"]
    vat_amount: Decimal

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "Transaction":
        return transaction_from_record(record)


def transaction_from_record(record: dict[str, Any]) -> Transaction:
    """Parse one transaction record into a normalized Transaction."""
    jurisdiction_raw = record.get("jurisdiction", record.get("country", ""))
    jurisdiction = str(jurisdiction_raw).strip()
    if not jurisdiction:
        raise ValueError("Record is missing a non-empty jurisdiction/country")

    tx_type_raw = record.get("transaction_type", record.get("type", "sale"))
    tx_type = str(tx_type_raw).strip().lower()
    if tx_type not in {"sale", "purchase"}:
        raise ValueError(f"Unsupported transaction_type: {tx_type}")

    if "vat_amount" in record and record["vat_amount"] is not None:
        vat_amount = _to_decimal(record["vat_amount"], "vat_amount")
    else:
        amount_raw = record.get("amount", record.get("net_amount"))
        if amount_raw is None:
            raise ValueError("Record is missing amount/net_amount")
        if "vat_rate" not in record:
            raise ValueError("Record is missing vat_rate")
        amount = _to_decimal(amount_raw, "amount")
        rate = _normalize_rate(record["vat_rate"])
        vat_amount = amount * rate

    if vat_amount < 0:
        raise ValueError("vat_amount cannot be negative")

    return Transaction(
        jurisdiction=jurisdiction.upper(),
        transaction_type=tx_type,
        vat_amount=_money(vat_amount),
    )


def _coerce_transaction(item: Transaction | dict[str, Any]) -> Transaction:
    if isinstance(item, Transaction):
        return item
    if isinstance(item, dict):
        return transaction_from_record(item)
    raise ValueError(f"Unsupported transaction item type: {type(item).__name__}")


def _calculate_vat_payable_decimal(
    transactions: Iterable[Transaction | dict[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}

    for index, item in enumerate(transactions):
        tx = _coerce_transaction(item)
        current = totals.get(tx.jurisdiction, Decimal("0"))

        if tx.transaction_type == "sale":
            current += tx.vat_amount
        elif tx.transaction_type == "purchase":
            current -= tx.vat_amount
        else:
            raise ValueError(
                f"transaction at index {index} has invalid transaction_type: "
                f"{tx.transaction_type}"
            )

        totals[tx.jurisdiction] = current

    result: dict[str, Decimal] = {}
    for jurisdiction in sorted(totals):
        amount = _money(totals[jurisdiction])
        if floor_at_zero and amount < 0:
            amount = Decimal("0.00")
        result[jurisdiction] = amount
    return result


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | dict[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Generate net VAT payable per jurisdiction as Decimal values."""
    return _calculate_vat_payable_decimal(transactions, floor_at_zero=floor_at_zero)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | dict[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, float]:
    """Calculate net VAT payable per jurisdiction as float values."""
    decimal_result = _calculate_vat_payable_decimal(
        transactions,
        floor_at_zero=floor_at_zero,
    )
    return {jurisdiction: float(amount) for jurisdiction, amount in decimal_result.items()}


def generate_vat_to_be_paid_per_jurisdiction(
    transactions: Iterable[Transaction | dict[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Alias matching alternate phrasing used in some integrations."""
    return generate_vat_payable_by_jurisdiction(
        transactions,
        floor_at_zero=floor_at_zero,
    )


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Transaction | dict[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Alias matching user-story wording."""
    return generate_vat_payable_by_jurisdiction(
        transactions,
        floor_at_zero=floor_at_zero,
    )


__all__ = [
    "Transaction",
    "transaction_from_record",
    "generate_vat_payable_by_jurisdiction",
    "calculate_vat_payable_by_jurisdiction",
    "generate_vat_to_be_paid_per_jurisdiction",
    "generate_vat_to_be_paid_for_each_jurisdiction",
]
