from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Mapping, Any


MONEY_PRECISION = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_jurisdiction(value: Any) -> str:
    jurisdiction = str(value).strip()
    if not jurisdiction:
        raise ValueError("Transaction jurisdiction is required.")
    return jurisdiction


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    vat_rates_by_jurisdiction: Mapping[str, Any],
) -> dict[str, Decimal]:
    """
    Generate VAT payable totals grouped by jurisdiction.

    Parameters
    ----------
    transactions:
        An iterable of transaction mappings. Each transaction must include:
        - "jurisdiction": jurisdiction code/name used for grouping and rate lookup
        - "taxable_amount": taxable base amount
        Optional:
        - "vat_rate": transaction-specific VAT rate (overrides jurisdiction default)
    vat_rates_by_jurisdiction:
        Mapping of jurisdiction to VAT rate (e.g. {"DE": "0.19"}).

    Returns
    -------
    dict[str, Decimal]
        VAT amount payable per jurisdiction, rounded to currency precision (2 decimals).
        Each transaction VAT is rounded (half-up) before aggregation.
    """

    vat_totals: dict[str, Decimal] = {}
    normalized_rates: dict[str, Decimal] = {
        _normalize_jurisdiction(jurisdiction): _to_decimal(rate, f"VAT rate for {jurisdiction!r}")
        for jurisdiction, rate in vat_rates_by_jurisdiction.items()
    }

    for transaction in transactions:
        jurisdiction = _normalize_jurisdiction(transaction.get("jurisdiction"))
        taxable_amount_value = transaction.get("taxable_amount")
        taxable_amount = (
            Decimal("0")
            if taxable_amount_value is None
            else _to_decimal(taxable_amount_value, "taxable_amount")
        )

        if "vat_rate" in transaction:
            vat_rate = _to_decimal(transaction.get("vat_rate"), "vat_rate")
        elif jurisdiction in normalized_rates:
            vat_rate = normalized_rates[jurisdiction]
        else:
            raise ValueError(f"Missing VAT rate for jurisdiction: {jurisdiction}")

        transaction_vat = (taxable_amount * vat_rate).quantize(
            MONEY_PRECISION, rounding=ROUND_HALF_UP
        )
        vat_totals[jurisdiction] = vat_totals.get(jurisdiction, Decimal("0")) + transaction_vat

    return {
        jurisdiction: total.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
        for jurisdiction, total in vat_totals.items()
    }
