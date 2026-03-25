"""Core VAT payable calculations."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable

OUTPUT_TYPES = {"sale", "output", "collected"}
INPUT_TYPES = {"purchase", "input", "deductible"}


def _to_decimal(value: Any, field_name: str, transaction_index: int) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid '{field_name}' in transaction #{transaction_index}: {value!r}"
        ) from exc


def _extract_vat_amount(transaction: dict[str, Any], transaction_index: int) -> Decimal:
    if transaction.get("vat_amount") is not None:
        return _to_decimal(transaction["vat_amount"], "vat_amount", transaction_index)

    amount = _to_decimal(transaction.get("amount"), "amount", transaction_index)
    vat_rate = _to_decimal(transaction.get("vat_rate"), "vat_rate", transaction_index)

    # Allow either a decimal fraction (0.20) or percentage (20).
    if vat_rate > Decimal("1"):
        vat_rate = vat_rate / Decimal("100")

    return amount * vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, Decimal]:
    """Calculate VAT payable per jurisdiction.

    VAT payable is computed as:
      output VAT (collected on sales) - input VAT (paid on purchases)
    """

    totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions, start=1):
        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(f"Invalid 'jurisdiction' in transaction #{index}")
        jurisdiction = jurisdiction.strip()

        transaction_type = transaction.get("type")
        if not isinstance(transaction_type, str):
            raise ValueError(f"Missing or invalid 'type' in transaction #{index}")
        normalized_type = transaction_type.strip().lower()

        vat_amount = _extract_vat_amount(transaction, index)

        if normalized_type in OUTPUT_TYPES:
            totals[jurisdiction] += vat_amount
        elif normalized_type in INPUT_TYPES:
            totals[jurisdiction] -= vat_amount
        else:
            raise ValueError(
                "Unsupported transaction type in transaction "
                f"#{index}: {transaction_type!r}"
            )

    return {
        jurisdiction: amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for jurisdiction, amount in sorted(totals.items())
    }


def serialize_totals(totals: dict[str, Decimal]) -> dict[str, str]:
    """Serialize decimal totals as fixed 2-decimal strings for JSON output."""
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in totals.items()}
