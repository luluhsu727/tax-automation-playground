"""Generate VAT payable amounts grouped by jurisdiction.

The core rule implemented here is:

    VAT payable = output VAT on sales - input VAT on purchases

Each transaction can provide either:
- ``vat_amount`` directly, or
- ``amount`` and ``vat_rate`` so VAT is computed as ``amount * vat_rate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

SALE_TYPES = {"sale", "sales", "output", "invoice", "customer_invoice"}
PURCHASE_TYPES = {
    "purchase",
    "purchases",
    "input",
    "bill",
    "vendor_bill",
    "expense",
}


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Aggregated VAT numbers for a jurisdiction."""

    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name!r} must be numeric, got {value!r}") from exc


def _normalize_jurisdiction(raw_value: Any) -> str:
    if raw_value is None:
        raise ValueError("'jurisdiction' is required for every transaction")
    jurisdiction = str(raw_value).strip()
    if not jurisdiction:
        raise ValueError("'jurisdiction' must be a non-empty string")
    return jurisdiction


def _is_purchase(transaction: Mapping[str, Any]) -> bool:
    if "is_purchase" in transaction:
        return bool(transaction["is_purchase"])
    tx_type = str(transaction.get("type", "sale")).strip().lower()
    if tx_type in PURCHASE_TYPES:
        return True
    if tx_type in SALE_TYPES:
        return False
    raise ValueError(
        "Unsupported transaction type "
        f"{tx_type!r}. Supported sale types: {sorted(SALE_TYPES)}; "
        f"purchase types: {sorted(PURCHASE_TYPES)}."
    )


def _transaction_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        if amount < 0:
            raise ValueError("'vat_amount' cannot be negative")
        return amount

    if "amount" not in transaction:
        raise ValueError("Transaction must include 'vat_amount' or 'amount'")
    if "vat_rate" not in transaction:
        raise ValueError("Transaction with 'amount' must include 'vat_rate'")

    amount = _to_decimal(transaction["amount"], "amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    if amount < 0:
        raise ValueError("'amount' cannot be negative")
    if vat_rate < 0:
        raise ValueError("'vat_rate' cannot be negative")
    return amount * vat_rate


def _round_decimal(amount: Decimal, precision: int) -> Decimal:
    quantum = Decimal("1").scaleb(-precision)
    return amount.quantize(quantum, rounding=ROUND_HALF_UP)


def summarize_vat_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
    *,
    precision: int = 2,
    clamp_negative_payable: bool = False,
) -> list[JurisdictionVatSummary]:
    """Summarize output/input/payable VAT for each jurisdiction.

    Args:
        transactions: Iterable of transaction mappings. Required key:
            ``jurisdiction``. Also required either:
            - ``vat_amount``, or
            - ``amount`` with ``vat_rate``.
            Direction is controlled by ``is_purchase`` (bool) or ``type``.
        precision: Number of decimal places in output values.
        clamp_negative_payable: If True, payable values below zero are set to 0.
            Useful when credits/refunds are handled outside this computation.
    """

    if precision < 0:
        raise ValueError("'precision' must be >= 0")

    grouped: dict[str, dict[str, Decimal]] = {}
    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            raise ValueError(
                "Each transaction must be a mapping/dict, "
                f"got {type(transaction).__name__}"
            )

        jurisdiction = _normalize_jurisdiction(transaction.get("jurisdiction"))
        vat_amount = _transaction_vat_amount(transaction)
        purchase = _is_purchase(transaction)

        bucket = grouped.setdefault(
            jurisdiction,
            {"output_vat": Decimal("0"), "input_vat": Decimal("0")},
        )
        if purchase:
            bucket["input_vat"] += vat_amount
        else:
            bucket["output_vat"] += vat_amount

    summaries: list[JurisdictionVatSummary] = []
    for jurisdiction in sorted(grouped):
        output_vat = _round_decimal(grouped[jurisdiction]["output_vat"], precision)
        input_vat = _round_decimal(grouped[jurisdiction]["input_vat"], precision)
        payable = output_vat - input_vat
        if clamp_negative_payable and payable < 0:
            payable = Decimal("0")
        payable = _round_decimal(payable, precision)

        summaries.append(
            JurisdictionVatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                vat_payable=payable,
            )
        )

    return summaries


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
    *,
    precision: int = 2,
    clamp_negative_payable: bool = False,
) -> dict[str, Decimal]:
    """Return VAT payable per jurisdiction."""

    return {
        summary.jurisdiction: summary.vat_payable
        for summary in summarize_vat_by_jurisdiction(
            transactions,
            precision=precision,
            clamp_negative_payable=clamp_negative_payable,
        )
    }


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
    *,
    precision: int = 2,
    clamp_negative_payable: bool = False,
) -> dict[str, Decimal]:
    """Alias for ``calculate_vat_payable_by_jurisdiction``."""

    return calculate_vat_payable_by_jurisdiction(
        transactions,
        precision=precision,
        clamp_negative_payable=clamp_negative_payable,
    )
