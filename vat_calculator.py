from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Mapping, MutableMapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: object, field_name: str) -> Decimal:
    """Convert a numeric-like value to Decimal with a clear error message."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_txn_type(raw_type: object) -> str:
    normalized = str(raw_type or "").strip().lower()
    if normalized in {"sale", "sales", "output", "output_vat"}:
        return "sale"
    if normalized in {"purchase", "purchases", "input", "input_vat", "expense"}:
        return "purchase"
    raise ValueError(
        "Transaction type must be one of sale/output or purchase/input. "
        f"Received: {raw_type!r}"
    )


def _extract_vat_amount(transaction: Mapping[str, object]) -> Decimal:
    if "vat_amount" in transaction:
        return _to_decimal(transaction["vat_amount"], "vat_amount")

    amount_key = "amount"
    if "amount" not in transaction:
        if "taxable_amount" in transaction:
            amount_key = "taxable_amount"
        elif "net_amount" in transaction:
            amount_key = "net_amount"
        else:
            raise ValueError(
                "Transaction must include either 'vat_amount' or a taxable amount "
                "('amount', 'taxable_amount', or 'net_amount')."
            )

    if "vat_rate" not in transaction:
        raise ValueError(
            "Transaction missing 'vat_rate'. Provide 'vat_amount' directly or include "
            "both a taxable amount and 'vat_rate'."
        )

    amount = _to_decimal(transaction[amount_key], amount_key)
    rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    return amount * rate


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, dict[str, float]]:
    """
    Aggregate VAT position by jurisdiction.

    Each transaction requires:
      - jurisdiction (str)
      - transaction type: one of sale/output or purchase/input
      - Either:
          - vat_amount
        or
          - amount/taxable_amount/net_amount and vat_rate

    Returns:
      {
        "<jurisdiction>": {
          "output_vat": <float>,
          "input_vat": <float>,
          "vat_payable": <float>,  # max(output_vat - input_vat, 0)
          "vat_credit": <float>,   # max(input_vat - output_vat, 0)
        },
        ...
      }
    """
    totals: MutableMapping[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for idx, transaction in enumerate(transactions, start=1):
        if not isinstance(transaction, Mapping):
            raise ValueError(
                f"Transaction at index {idx} must be a mapping/dict. "
                f"Received: {type(transaction).__name__}"
            )

        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} is missing 'jurisdiction'.")

        raw_type = transaction.get("type", transaction.get("transaction_type"))
        txn_type = _normalize_txn_type(raw_type)
        vat_amount = _extract_vat_amount(transaction)

        if txn_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, float]] = {}
    for jurisdiction, values in totals.items():
        output_vat = values["output_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        input_vat = values["input_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        vat_payable = max(output_vat - input_vat, Decimal("0")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        vat_credit = max(input_vat - output_vat, Decimal("0")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )

        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
            "vat_credit": float(vat_credit),
        }

    return result


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> dict[str, dict[str, float]]:
    """Alias with a descriptive name matching business wording."""
    return generate_vat_payable_by_jurisdiction(transactions)
