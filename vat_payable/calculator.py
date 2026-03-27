"""Core VAT payable calculations for dict-like transaction payloads."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Iterable

from vat_core import INPUT_TYPES, OUTPUT_TYPES, VatError, money, normalize_jurisdiction, to_decimal, to_rate


def _extract_vat_amount(transaction: dict[str, Any], transaction_index: int) -> Decimal:
    if transaction.get("vat_amount") is not None:
        return to_decimal(transaction["vat_amount"], field_name=f"vat_amount#{transaction_index}")

    amount = to_decimal(transaction.get("amount"), field_name=f"amount#{transaction_index}")
    vat_rate = to_rate(transaction.get("vat_rate"), field_name=f"vat_rate#{transaction_index}")
    return amount * vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, Decimal]:
    """Calculate VAT payable per jurisdiction.

    VAT payable is:
      output VAT (sales) - input VAT (purchases)
    """
    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions, start=1):
        jurisdiction_raw = transaction.get("jurisdiction")
        if not isinstance(jurisdiction_raw, str) or not jurisdiction_raw.strip():
            raise VatError(f"Invalid 'jurisdiction' in transaction #{index}")
        jurisdiction = normalize_jurisdiction(jurisdiction_raw)

        transaction_type = transaction.get("type", transaction.get("transaction_type"))
        normalized_type = str(transaction_type).strip().lower()

        vat_amount = _extract_vat_amount(transaction, index)

        if normalized_type in OUTPUT_TYPES:
            totals[jurisdiction] += vat_amount
        elif normalized_type in INPUT_TYPES:
            totals[jurisdiction] -= vat_amount
        else:
            raise VatError(f"Unsupported transaction type in transaction #{index}: {transaction_type!r}")

    return {jurisdiction: money(amount) for jurisdiction, amount in sorted(totals.items())}


def serialize_totals(totals: dict[str, Decimal]) -> dict[str, str]:
    """Serialize decimal totals as fixed 2-decimal strings for JSON output."""
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in totals.items()}
