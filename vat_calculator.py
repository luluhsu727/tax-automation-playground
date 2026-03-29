"""VAT calculator utilities."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Mapping


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert a value to Decimal with a clear error for bad data."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a numeric value.") from exc


def calculate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Calculate VAT totals and payable VAT for each jurisdiction.

    Each transaction must contain:
    - jurisdiction: non-empty string
    - vat_type: "output" or "input"
    - vat_amount: numeric (int/float/Decimal-compatible)
    """

    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            raise TypeError("Each transaction must be a mapping/dictionary.")

        missing_keys = {"jurisdiction", "vat_type", "vat_amount"} - transaction.keys()
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"Transaction is missing required keys: {missing}")

        jurisdiction = transaction["jurisdiction"]
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError("jurisdiction must be a non-empty string.")
        jurisdiction = jurisdiction.strip()

        vat_type = str(transaction["vat_type"]).strip().lower()
        if vat_type not in {"output", "input"}:
            raise ValueError('vat_type must be either "output" or "input".')

        vat_amount = _to_decimal(transaction["vat_amount"], field_name="vat_amount")
        if vat_amount < 0:
            raise ValueError("vat_amount must be non-negative.")

        bucket = "output_vat" if vat_type == "output" else "input_vat"
        totals[jurisdiction][bucket] += vat_amount

    result: Dict[str, Dict[str, float]] = {}
    for jurisdiction, jurisdiction_totals in totals.items():
        output_vat = jurisdiction_totals["output_vat"]
        input_vat = jurisdiction_totals["input_vat"]
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(output_vat - input_vat),
        }

    return result
