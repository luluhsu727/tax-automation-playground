from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Iterable, Literal, Mapping, TypedDict

TWOPLACES = Decimal("0.01")


class VatComputationError(ValueError):
    """Raised when transaction data is invalid for VAT computation."""


class Transaction(TypedDict, total=False):
    jurisdiction: str
    amount: Decimal | int | float | str
    net_amount: Decimal | int | float | str
    vat_rate: Decimal | int | float | str
    transaction_type: Literal["sale", "purchase"]
    vat_amount: Decimal | int | float | str | None


@dataclass(frozen=True)
class JurisdictionVatTotals:
    output_vat: Decimal
    input_vat: Decimal
    vat_to_be_paid: Decimal


def _to_decimal(value: Decimal | int | float | str, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise VatComputationError(f"Invalid {field_name} value: {value!r}") from exc


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_rate(rate: Decimal | int | float | str) -> Decimal:
    rate_decimal = _to_decimal(rate, "vat_rate")
    if rate_decimal < 0:
        raise VatComputationError("VAT rate cannot be negative")
    return rate_decimal / Decimal("100") if rate_decimal > 1 else rate_decimal


def _compute_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    explicit_vat = transaction.get("vat_amount")
    if explicit_vat not in (None, ""):
        vat_amount = _to_decimal(explicit_vat, "vat_amount")
        if vat_amount < 0:
            raise VatComputationError("VAT amount cannot be negative")
        return _to_money(vat_amount)

    raw_amount = transaction.get("amount", transaction.get("net_amount"))
    if raw_amount in (None, ""):
        raise VatComputationError("Missing required field: amount (or net_amount)")
    if "vat_rate" not in transaction:
        raise VatComputationError("Missing required field: vat_rate")

    amount = _to_decimal(raw_amount, "amount")
    if amount < 0:
        raise VatComputationError("Amount cannot be negative")
    rate = _normalize_rate(transaction["vat_rate"])
    return _to_money(amount * rate)


def _accumulate(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
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

    return grouped


def generate_vat_to_be_paid(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, JurisdictionVatTotals]:
    """
    Generate VAT totals for each jurisdiction.

    VAT to be paid is computed as:
      output_vat - input_vat
    """
    grouped = _accumulate(transactions)
    result: dict[str, JurisdictionVatTotals] = {}

    for jurisdiction in sorted(grouped):
        output_vat = _to_money(grouped[jurisdiction]["output_vat"])
        input_vat = _to_money(grouped[jurisdiction]["input_vat"])
        vat_to_be_paid = _to_money(output_vat - input_vat)
        result[jurisdiction] = JurisdictionVatTotals(
            output_vat=output_vat,
            input_vat=input_vat,
            vat_to_be_paid=vat_to_be_paid,
        )

    return result


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """
    Calculate output/input VAT and VAT payable grouped by jurisdiction.

    This function returns float values to make serialization and CLI rendering easy.
    """
    raw = generate_vat_to_be_paid(transactions)
    result: dict[str, dict[str, float]] = {}

    for jurisdiction, totals in raw.items():
        result[jurisdiction] = {
            "output_vat": float(totals.output_vat),
            "input_vat": float(totals.input_vat),
            "vat_to_be_paid": float(totals.vat_to_be_paid),
            "vat_payable": float(totals.vat_to_be_paid),
        }

    return result
