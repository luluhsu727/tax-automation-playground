"""Utilities to calculate VAT payable per jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")
OUTPUT_TYPES = {"sale", "sales", "output"}
INPUT_TYPES = {"purchase", "purchases", "input", "expense", "expenses"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _to_rate(value: Any) -> Decimal:
    """Accept VAT rates as either decimal fractions or percentages."""
    rate = _to_decimal(value, "vat_rate")
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


def _normalize_transaction_type(value: Any) -> str:
    transaction_type = str(value).strip().lower()
    if transaction_type in OUTPUT_TYPES:
        return "output"
    if transaction_type in INPUT_TYPES:
        return "input"
    raise ValueError(
        "transaction_type must be one of "
        f"{sorted(OUTPUT_TYPES | INPUT_TYPES)}. Got: {value!r}"
    )


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Decimal | str]]:
    """Generate VAT payable summary for each jurisdiction.

    Each transaction must contain:
    - jurisdiction (str)
    - transaction_type (sale/output or purchase/input)
    - vat_amount OR (taxable_amount and vat_rate)
    """

    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for tx in transactions:
        jurisdiction = str(tx.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("jurisdiction is required for each transaction")

        tx_type = _normalize_transaction_type(tx.get("transaction_type", ""))

        if tx.get("vat_amount") is not None:
            vat_amount = _to_decimal(tx["vat_amount"], "vat_amount")
        else:
            if tx.get("taxable_amount") is None or tx.get("vat_rate") is None:
                raise ValueError(
                    "Each transaction must provide vat_amount "
                    "or both taxable_amount and vat_rate"
                )
            taxable_amount = _to_decimal(tx["taxable_amount"], "taxable_amount")
            vat_rate = _to_rate(tx["vat_rate"])
            vat_amount = taxable_amount * vat_rate

        if vat_amount < 0:
            raise ValueError("vat_amount cannot be negative")

        totals[jurisdiction][f"{tx_type}_vat"] += vat_amount

    result: list[dict[str, Decimal | str]] = []
    for jurisdiction in sorted(totals):
        output_vat = _quantize(totals[jurisdiction]["output_vat"])
        input_vat = _quantize(totals[jurisdiction]["input_vat"])
        net_vat = _quantize(output_vat - input_vat)

        result.append(
            {
                "jurisdiction": jurisdiction,
                "output_vat": output_vat,
                "input_vat": input_vat,
                "net_vat": net_vat,
                "vat_payable": _quantize(max(net_vat, Decimal("0"))),
                "vat_refundable": _quantize(max(-net_vat, Decimal("0"))),
            }
        )

    return result
