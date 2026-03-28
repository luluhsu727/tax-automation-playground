"""Utilities to compute VAT payable by jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

_SALE_TYPES = {"sale", "output"}
_PURCHASE_TYPES = {"purchase", "input"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid {field_name!r} value: {value!r}") from exc


def _normalize_rate(raw_rate: Any) -> Decimal:
    """
    Normalize VAT rate to a fraction.

    Accepted formats:
    - 0.2 for 20%
    - 20 for 20%
    """
    rate = _to_decimal(raw_rate, "vat_rate")
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


def _quantize(amount: Decimal, precision: int) -> Decimal:
    quantizer = Decimal("1").scaleb(-precision)
    return amount.quantize(quantizer, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    precision: int = 2,
) -> dict[str, float]:
    """
    Generate VAT payable grouped by jurisdiction.

    Each transaction must include:
    - jurisdiction (str)
    - transaction_type: sale/output or purchase/input
    - either vat_amount OR (amount and vat_rate)

    VAT payable formula per jurisdiction:
        sum(output VAT) - sum(input VAT)
    """
    if precision < 0:
        raise ValueError("precision must be zero or greater")

    totals: dict[str, Decimal] = {}

    for txn in transactions:
        jurisdiction = str(txn.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction")

        txn_type = str(txn.get("transaction_type", "")).strip().lower()
        if txn_type in _SALE_TYPES:
            sign = Decimal("1")
        elif txn_type in _PURCHASE_TYPES:
            sign = Decimal("-1")
        else:
            raise ValueError(
                f"Unsupported transaction_type {txn_type!r}; "
                "expected sale/output/purchase/input"
            )

        if "vat_amount" in txn and txn["vat_amount"] is not None:
            vat_amount = _to_decimal(txn["vat_amount"], "vat_amount")
        else:
            if "amount" not in txn or "vat_rate" not in txn:
                raise ValueError(
                    "Transaction must include vat_amount or both amount and vat_rate"
                )
            amount = _to_decimal(txn["amount"], "amount")
            if amount < 0:
                raise ValueError("amount cannot be negative")
            rate = _normalize_rate(txn["vat_rate"])
            vat_amount = amount * rate

        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + (sign * vat_amount)

    return {
        jurisdiction: float(_quantize(total, precision))
        for jurisdiction, total in sorted(totals.items())
    }
