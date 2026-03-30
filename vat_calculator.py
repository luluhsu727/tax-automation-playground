"""Utilities for generating VAT payable per jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Convert int/float/str/Decimal values to Decimal safely."""
    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Sequence[Mapping[str, Any]],
    jurisdiction_rates: Mapping[str, Any],
    default_rate: Any | None = None,
) -> dict[str, dict[str, Decimal]]:
    """
    Generate VAT payable for each jurisdiction.

    Each transaction must include:
      - jurisdiction: str
      - amount: number-like
      - transaction_type: one of {"sale", "purchase"}

    Optional transaction field:
      - vat_rate: overrides jurisdiction-level rate for this transaction

    VAT payable per jurisdiction is:
      output_vat_on_sales - input_vat_on_purchases
    """
    totals: dict[str, dict[str, Decimal]] = {}

    for tx in transactions:
        jurisdiction = tx.get("jurisdiction")
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction")

        amount = _to_decimal(tx.get("amount", 0))
        if amount < 0:
            raise ValueError("Transaction amount cannot be negative")

        tx_type = str(tx.get("transaction_type", "")).lower().strip()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                "transaction_type must be either 'sale' or 'purchase'"
            )

        if "vat_rate" in tx and tx["vat_rate"] is not None:
            rate = _to_decimal(tx["vat_rate"])
        elif jurisdiction in jurisdiction_rates:
            rate = _to_decimal(jurisdiction_rates[jurisdiction])
        elif default_rate is not None:
            rate = _to_decimal(default_rate)
        else:
            raise ValueError(
                f"No VAT rate provided for jurisdiction '{jurisdiction}'"
            )

        if rate < 0:
            raise ValueError("VAT rate cannot be negative")

        vat_amount = amount * rate
        if jurisdiction not in totals:
            totals[jurisdiction] = {
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
                "vat_payable": Decimal("0"),
            }

        if tx_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    for jurisdiction, bucket in totals.items():
        output_vat = _round_money(bucket["output_vat"])
        input_vat = _round_money(bucket["input_vat"])
        totals[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _round_money(output_vat - input_vat),
        }

    return totals


# Alias with wording from the task for discoverability.
generate_vat_to_be_paid_for_each_jurisdiction = generate_vat_payable_by_jurisdiction
