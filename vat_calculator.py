"""VAT payable calculator by jurisdiction.

This module computes VAT to be paid per jurisdiction from a list of transactions.
Each transaction must include:
  - jurisdiction (str)
  - transaction_type (sale or purchase). Alias: type
  - net_amount (number-like). Alias: amount
  - vat_rate (decimal between 0 and 1)
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


SALE = "sale"
PURCHASE = "purchase"
VALID_TRANSACTION_TYPES = {SALE, PURCHASE}
MONEY_QUANT = Decimal("0.01")


def _to_decimal(value: Any, field_name: str, tx_index: int) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(
            f"Transaction {tx_index}: field '{field_name}' must be numeric."
        ) from exc


def _round_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_vat_to_be_paid(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Calculate VAT payable for each jurisdiction.

    VAT to be paid = output VAT (sales) - input VAT (purchases).

    Returns:
        {
          "<jurisdiction>": {
            "output_vat": Decimal,
            "input_vat": Decimal,
            "vat_to_be_paid": Decimal,
          },
          ...
        }
    """

    aggregates: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for idx, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(
                f"Transaction {idx}: field 'jurisdiction' must be a non-empty string."
            )
        jurisdiction = jurisdiction.strip()

        transaction_type = transaction.get("transaction_type", transaction.get("type"))
        if transaction_type not in VALID_TRANSACTION_TYPES:
            raise ValueError(
                f"Transaction {idx}: field 'transaction_type' must be one of "
                f"{sorted(VALID_TRANSACTION_TYPES)}."
            )

        raw_amount = transaction.get("net_amount", transaction.get("amount"))
        if raw_amount is None:
            raise ValueError(
                f"Transaction {idx}: field 'net_amount' (or alias 'amount') is required."
            )
        net_amount = _to_decimal(raw_amount, "net_amount", idx)
        if net_amount < 0:
            raise ValueError(f"Transaction {idx}: field 'net_amount' cannot be negative.")

        if "vat_rate" not in transaction:
            raise ValueError(f"Transaction {idx}: field 'vat_rate' is required.")
        vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate", idx)
        if vat_rate < 0 or vat_rate > 1:
            raise ValueError(
                f"Transaction {idx}: field 'vat_rate' must be between 0 and 1."
            )

        # VAT is rounded per transaction line item.
        vat_amount = _round_money(net_amount * vat_rate)

        if transaction_type == SALE:
            aggregates[jurisdiction]["output_vat"] += vat_amount
        else:
            aggregates[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(aggregates):
        output_vat = _round_money(aggregates[jurisdiction]["output_vat"])
        input_vat = _round_money(aggregates[jurisdiction]["input_vat"])
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_to_be_paid": _round_money(output_vat - input_vat),
        }

    return result
