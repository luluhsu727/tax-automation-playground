from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert input to Decimal with clear validation errors."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _resolve_vat_amount(transaction: Mapping[str, Any], index: int) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return _to_decimal(transaction["vat_amount"], f"transactions[{index}].vat_amount")

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            f"transactions[{index}] must provide either 'vat_amount' or both "
            "'amount' and 'vat_rate'"
        )

    amount = _to_decimal(transaction["amount"], f"transactions[{index}].amount")
    vat_rate = _to_decimal(transaction["vat_rate"], f"transactions[{index}].vat_rate")
    return amount * vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]], *, decimal_places: int = 2
) -> dict[str, Decimal]:
    """
    Aggregate VAT to be paid for each jurisdiction.

    Each transaction must include:
      - jurisdiction: str
      - either:
          - vat_amount, or
          - amount and vat_rate (where vat_rate is a decimal rate, e.g. 0.2 for 20%)

    Returns:
      A dictionary of jurisdiction -> total VAT payable, rounded with HALF_UP.
    """
    if decimal_places < 0:
        raise ValueError("decimal_places must be >= 0")

    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for index, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(
                f"transactions[{index}].jurisdiction must be a non-empty string"
            )

        vat_amount = _resolve_vat_amount(transaction, index)
        totals[jurisdiction.strip()] += vat_amount

    quantizer = Decimal("1").scaleb(-decimal_places)
    rounded_totals = {
        key: value.quantize(quantizer, rounding=ROUND_HALF_UP)
        for key, value in sorted(totals.items())
    }
    return rounded_totals
