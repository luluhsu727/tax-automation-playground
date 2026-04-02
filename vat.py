from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, MutableMapping


_OUTPUT_TYPES = {"sale", "output", "output_vat"}
_INPUT_TYPES = {"purchase", "input", "input_vat"}
_TWO_DP = Decimal("0.01")


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _resolve_vat_amount(transaction: Mapping[str, object]) -> Decimal:
    if "vat_amount" in transaction:
        return _to_decimal(transaction["vat_amount"], "vat_amount")

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction must include either 'vat_amount' or both 'amount' and 'vat_rate'."
        )

    amount = _to_decimal(transaction["amount"], "amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    return amount * vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, float]:
    """
    Calculate net VAT payable (output VAT - input VAT) for each jurisdiction.

    Each transaction must contain:
      - jurisdiction: jurisdiction code/name
      - type | transaction_type | direction: sale/output vs purchase/input
      - vat_amount OR (amount and vat_rate)
    """
    totals: MutableMapping[str, Decimal] = {}

    for transaction in transactions:
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty 'jurisdiction'.")

        tx_type = (
            transaction.get("type")
            or transaction.get("transaction_type")
            or transaction.get("direction")
        )
        if not tx_type:
            raise ValueError(
                "Each transaction must include 'type', 'transaction_type', or 'direction'."
            )

        tx_type_normalized = str(tx_type).strip().lower()
        vat_amount = _resolve_vat_amount(transaction)

        if tx_type_normalized in _OUTPUT_TYPES:
            signed_vat = vat_amount
        elif tx_type_normalized in _INPUT_TYPES:
            signed_vat = -vat_amount
        else:
            raise ValueError(
                "Transaction type must be one of "
                f"{sorted(_OUTPUT_TYPES | _INPUT_TYPES)}. Got: {tx_type!r}"
            )

        jurisdiction_key = str(jurisdiction)
        totals[jurisdiction_key] = totals.get(jurisdiction_key, Decimal("0")) + signed_vat

    return {
        jurisdiction: float(total.quantize(_TWO_DP, rounding=ROUND_HALF_UP))
        for jurisdiction, total in totals.items()
    }


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, float]:
    """Backward-compatible alias for calculate_vat_payable_by_jurisdiction."""
    return calculate_vat_payable_by_jurisdiction(transactions)
