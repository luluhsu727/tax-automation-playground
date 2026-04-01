from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Literal, TypedDict

TWOPLACES = Decimal("0.01")


class VatComputationError(ValueError):
    """Raised when transaction data is invalid for VAT computation."""


class Transaction(TypedDict, total=False):
    jurisdiction: str
    amount: Decimal | int | float | str
    vat_rate: Decimal | int | float | str
    transaction_type: Literal["sale", "purchase"]
    vat_amount: Decimal | int | float | str | None


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_rate(rate: Decimal | int | float | str) -> Decimal:
    rate_decimal = _to_decimal(rate)
    if rate_decimal < 0:
        raise VatComputationError("VAT rate cannot be negative")
    return rate_decimal / Decimal("100") if rate_decimal > 1 else rate_decimal


def _compute_vat_amount(transaction: Transaction) -> Decimal:
    explicit_vat = transaction.get("vat_amount")
    if explicit_vat not in (None, ""):
        vat_amount = _to_decimal(explicit_vat)
    else:
        try:
            amount = _to_decimal(transaction["amount"])
            rate = _normalize_rate(transaction["vat_rate"])
        except KeyError as exc:
            raise VatComputationError(f"Missing required field: {exc.args[0]}") from exc
        vat_amount = amount * rate
    return _to_money(vat_amount)


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, dict[str, float]]:
    """Compute output VAT, input VAT, and VAT payable by jurisdiction."""
    grouped: dict[str, dict[str, Decimal]] = {}

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise VatComputationError("Transaction has empty jurisdiction")

        tx_type = str(transaction.get("transaction_type", "")).strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise VatComputationError(
                f"Unsupported transaction_type '{transaction.get('transaction_type')}'. "
                "Use 'sale' or 'purchase'."
            )

        vat_amount = _compute_vat_amount(transaction)
        bucket = grouped.setdefault(
            jurisdiction,
            {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")},
        )
        if tx_type == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: dict[str, dict[str, float]] = {}
    for jurisdiction in sorted(grouped):
        output_vat = _to_money(grouped[jurisdiction]["output_vat"])
        input_vat = _to_money(grouped[jurisdiction]["input_vat"])
        vat_payable = _to_money(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }

    return result
