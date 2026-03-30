"""VAT payable calculation utilities.

This module calculates VAT balances per jurisdiction by combining:
- output VAT (sales VAT collected)
- input VAT (recoverable purchase VAT paid)

The net balance is:
    net_vat = output_vat - input_vat

A positive value means VAT is payable. A negative value means a refundable
credit position.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Safely convert common numeric inputs to Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_direction(raw_direction: str) -> str:
    """Normalize transaction direction to 'output' or 'input'."""
    direction = raw_direction.strip().lower()
    if direction in {"sale", "sales", "output", "out"}:
        return "output"
    if direction in {"purchase", "purchases", "input", "in"}:
        return "input"
    raise ValueError(
        "Transaction direction must be one of: "
        "sale/sales/output/out or purchase/purchases/input/in"
    )


def _line_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    """Resolve VAT amount from either explicit vat_amount or amount+vat_rate."""
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return abs(_to_decimal(transaction["vat_amount"]))

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction requires either 'vat_amount' or both "
            "'amount' and 'vat_rate'."
        )

    amount = _to_decimal(transaction["amount"])
    vat_rate = _to_decimal(transaction["vat_rate"])
    return abs(amount * vat_rate)


def calculate_vat_summary_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Return output/input/net VAT by jurisdiction.

    Expected transaction fields:
    - jurisdiction (required)
    - type or direction (required): sale|purchase (or output|input aliases)
    - vat_amount (optional if amount and vat_rate provided)
    - amount (optional if vat_amount provided)
    - vat_rate (optional if vat_amount provided)
    - recoverable (optional, purchase-only, defaults to True)

    Returns:
        {
            "DE": {
                "output_vat": Decimal("190.00"),
                "input_vat": Decimal("57.00"),
                "net_vat": Decimal("133.00"),
            },
            ...
        }
    """
    summary: dict[str, dict[str, Decimal]] = {}

    for transaction in transactions:
        jurisdiction_raw = transaction.get("jurisdiction")
        if not jurisdiction_raw:
            raise ValueError("Each transaction must include 'jurisdiction'.")

        jurisdiction = str(jurisdiction_raw).strip().upper()
        raw_direction = transaction.get("type") or transaction.get("direction")
        if raw_direction is None:
            raise ValueError("Each transaction must include 'type' or 'direction'.")

        direction = _normalize_direction(str(raw_direction))
        vat_amount = _line_vat_amount(transaction)

        if jurisdiction not in summary:
            summary[jurisdiction] = {
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
                "net_vat": Decimal("0"),
            }

        if direction == "output":
            summary[jurisdiction]["output_vat"] += vat_amount
        else:
            recoverable = bool(transaction.get("recoverable", True))
            if recoverable:
                summary[jurisdiction]["input_vat"] += vat_amount

    for jurisdiction_data in summary.values():
        jurisdiction_data["net_vat"] = (
            jurisdiction_data["output_vat"] - jurisdiction_data["input_vat"]
        )

    return summary


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    clamp_negative: bool = False,
    quantize: Decimal = TWOPLACES,
) -> dict[str, Decimal]:
    """Return net VAT per jurisdiction (payable if positive).

    Args:
        transactions: Iterable of VAT transactions.
        clamp_negative: If True, credit balances are returned as zero.
        quantize: Decimal precision for returned values. Defaults to cents.
    """
    summary = calculate_vat_summary_by_jurisdiction(transactions)
    result: dict[str, Decimal] = {}

    for jurisdiction, totals in summary.items():
        net_vat = totals["net_vat"]
        if clamp_negative and net_vat < 0:
            net_vat = Decimal("0")
        result[jurisdiction] = net_vat.quantize(quantize, rounding=ROUND_HALF_UP)

    return result


def generate_vat_payable_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Convenience API for VAT payable-only output (no negative values)."""
    return calculate_vat_payable_by_jurisdiction(transactions, clamp_negative=True)
