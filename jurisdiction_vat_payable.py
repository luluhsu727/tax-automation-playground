#!/usr/bin/env python3
"""Compatibility API for VAT payable by jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

from vat_payable import load_transactions, vat_payable_by_jurisdiction

TWOPLACES = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _to_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for '{field_name}': {raw_value}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    return rate / Decimal("100") if rate > 1 else rate


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """
    Aggregate taxable amount and VAT payable totals by jurisdiction.

    Output rows are sorted by jurisdiction with string currency fields.
    """
    normalized_transactions = list(transactions)
    payable = vat_payable_by_jurisdiction(normalized_transactions)
    totals: dict[str, Decimal] = {}
    rates: dict[str, Decimal] = {}

    for tx in normalized_transactions:
        jurisdiction = str(tx.get("jurisdiction") or tx.get("country") or "").strip().upper()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction.")

        amount_raw = (
            tx.get("amount")
            if tx.get("amount") is not None
            else tx.get("taxable_amount", tx.get("net_amount", tx.get("revenue")))
        )
        amount = _to_decimal(amount_raw, "amount")
        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + amount

        raw_rate = tx.get("vat_rate", tx.get("rate"))
        if raw_rate is not None and str(raw_rate).strip() != "":
            rates[jurisdiction] = _normalize_rate(_to_decimal(raw_rate, "vat_rate"))

    rows: list[dict[str, str]] = []
    for jurisdiction in sorted(payable):
        taxable_total = _money(totals.get(jurisdiction, Decimal("0")))
        payable_total = _money(Decimal(str(payable[jurisdiction])))
        if taxable_total:
            effective_rate = _money(payable_total / taxable_total)
        else:
            effective_rate = rates.get(jurisdiction, Decimal("0"))
        rows.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{payable_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )
    return rows


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Return VAT-to-be-paid total per jurisdiction as Decimal."""
    payable = vat_payable_by_jurisdiction(transactions)
    return {jurisdiction: Decimal(str(value)) for jurisdiction, value in payable.items()}


__all__ = [
    "compute_vat_payable_by_jurisdiction",
    "generate_vat_to_be_paid_for_each_jurisdiction",
    "load_transactions",
    "Path",
]
