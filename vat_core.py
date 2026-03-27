"""Shared VAT helpers used by compatibility modules.

The repository hosts multiple historical module layouts for the same problem.
This file centralizes Decimal handling and VAT normalization to keep behavior
consistent across those layouts.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

TWOPLACES = Decimal("0.01")

OUTPUT_TYPES = {"sale", "output", "collected"}
INPUT_TYPES = {"purchase", "input", "deductible"}


class VatError(ValueError):
    """Raised when VAT data is invalid."""


def to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert value to Decimal with a consistent error."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise VatError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def money(value: Decimal) -> Decimal:
    """Round using accounting-safe half-up logic."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def to_rate(value: Any, *, field_name: str) -> Decimal:
    """Normalize VAT rate from either fraction (0.2) or percent (20)."""
    rate = to_decimal(value, field_name=field_name)
    if rate > Decimal("1"):
        rate = rate / Decimal("100")
    return rate


def normalize_jurisdiction(value: Any, *, field_name: str = "jurisdiction") -> str:
    code = str(value).strip().upper()
    if not code:
        raise VatError(f"Invalid '{field_name}' value: {value!r}")
    return code


def normalize_tx_type(value: Any) -> str:
    tx_type = str(value).strip().lower()
    if tx_type in OUTPUT_TYPES:
        return "sale"
    if tx_type in INPUT_TYPES:
        return "purchase"
    raise VatError(f"Unsupported transaction type: {value!r}")
