"""Utilities to calculate VAT payable by jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Iterable, Mapping


CENT = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_rate(value: Any, field_name: str) -> Decimal:
    """Accept a decimal ratio (0.2) or percentage (20) and normalize to ratio."""
    rate = _to_decimal(value, field_name)
    if rate < 0:
        raise ValueError(f"{field_name} cannot be negative: {value!r}")

    if rate > 1:
        if rate <= 100:
            rate = rate / Decimal("100")
        else:
            raise ValueError(f"{field_name} is too large: {value!r}")
    return rate


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    vat_rates_by_jurisdiction: Mapping[str, Any],
) -> dict[str, dict[str, Decimal]]:
    """
    Generate VAT report with payable amount for each jurisdiction.

    Expected transaction fields:
      - jurisdiction: str
      - type: "sale" or "purchase"
      - amount: numeric
      - vat_rate (optional): overrides jurisdiction default (0.2 or 20)
    """
    rates = {
        jurisdiction: _normalize_rate(rate, f"vat rate for {jurisdiction}")
        for jurisdiction, rate in vat_rates_by_jurisdiction.items()
    }

    report: dict[str, dict[str, Decimal]] = {
        jurisdiction: {
            "taxable_sales": Decimal("0"),
            "taxable_purchases": Decimal("0"),
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
        for jurisdiction in rates
    }

    for tx in transactions:
        jurisdiction = tx.get("jurisdiction")
        if not jurisdiction:
            raise ValueError(f"Transaction missing jurisdiction: {tx!r}")

        tx_type = str(tx.get("type", "")).lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(f"Unsupported transaction type: {tx_type!r}")

        amount = _to_decimal(tx.get("amount"), "amount")
        tx_rate = tx.get("vat_rate")
        if tx_rate is None:
            if jurisdiction not in rates:
                raise ValueError(
                    f"No default VAT rate configured for jurisdiction {jurisdiction!r}"
                )
            rate = rates[jurisdiction]
        else:
            rate = _normalize_rate(tx_rate, f"vat_rate in transaction {tx!r}")

        if jurisdiction not in report:
            report[jurisdiction] = {
                "taxable_sales": Decimal("0"),
                "taxable_purchases": Decimal("0"),
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
            }

        jurisdiction_totals = report[jurisdiction]
        vat_amount = amount * rate
        if tx_type == "sale":
            jurisdiction_totals["taxable_sales"] += amount
            jurisdiction_totals["output_vat"] += vat_amount
        else:
            jurisdiction_totals["taxable_purchases"] += amount
            jurisdiction_totals["input_vat"] += vat_amount

    finalized: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(report):
        totals = report[jurisdiction]
        output_vat = _money(totals["output_vat"])
        input_vat = _money(totals["input_vat"])
        finalized[jurisdiction] = {
            "taxable_sales": _money(totals["taxable_sales"]),
            "taxable_purchases": _money(totals["taxable_purchases"]),
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _money(output_vat - input_vat),
        }
    return finalized
