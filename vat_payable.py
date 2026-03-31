"""VAT payable calculation utilities.

This module provides a small, dependency-free helper for computing VAT
to be paid for each jurisdiction based on transaction-level records.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Literal, Mapping

TransactionType = Literal["sale", "purchase"]

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any) -> Decimal:
    """Convert supported numeric-like values to Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_money(value: Decimal, decimal_places: int) -> Decimal:
    """Quantize money values to the requested decimal places."""
    if decimal_places < 0:
        raise ValueError("decimal_places must be >= 0")

    exponent = Decimal("1").scaleb(-decimal_places)
    return value.quantize(exponent, rounding=ROUND_HALF_UP)


def _extract_vat_amount(record: Mapping[str, Any]) -> Decimal:
    """Extract VAT amount from a record.

    Priority:
      1) explicit "vat_amount"
      2) taxable amount * vat_rate
    """
    if "vat_amount" in record and record["vat_amount"] is not None:
        return _to_decimal(record["vat_amount"])

    if "taxable_amount" not in record:
        raise ValueError(
            "record must include either vat_amount or taxable_amount"
        )
    if "vat_rate" not in record:
        raise ValueError("record with taxable_amount must include vat_rate")

    taxable_amount = _to_decimal(record["taxable_amount"])
    vat_rate = _to_decimal(record["vat_rate"])
    return taxable_amount * vat_rate


def calculate_vat_to_be_paid_by_jurisdiction(
    records: Iterable[Mapping[str, Any]],
    *,
    decimal_places: int = 2,
) -> Dict[str, Dict[str, Decimal | str]]:
    """Generate VAT payable for each jurisdiction.

    Each record must include:
      - jurisdiction: str
      - transaction_type: "sale" or "purchase"
      - either:
          * vat_amount, or
          * taxable_amount + vat_rate

    Rules:
      - sale VAT contributes to output_vat
      - purchase VAT contributes to input_vat
      - net_vat = output_vat - input_vat
      - vat_to_be_paid = max(net_vat, 0)
      - refund_due = max(-net_vat, 0)
    """
    aggregates: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for idx, record in enumerate(records):
        jurisdiction = record.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(f"record[{idx}] has invalid jurisdiction")

        transaction_type = record.get("transaction_type")
        if transaction_type not in ("sale", "purchase"):
            raise ValueError(
                f"record[{idx}] has invalid transaction_type: {transaction_type!r}"
            )

        vat_amount = _extract_vat_amount(record)
        if vat_amount < 0:
            raise ValueError(f"record[{idx}] has negative VAT amount")

        key: TransactionType = transaction_type  # narrow type for clarity
        bucket = aggregates[jurisdiction.strip()]
        if key == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: Dict[str, Dict[str, Decimal | str]] = {}
    for jurisdiction, values in sorted(aggregates.items()):
        output_vat = _quantize_money(values["output_vat"], decimal_places)
        input_vat = _quantize_money(values["input_vat"], decimal_places)
        net_vat = _quantize_money(output_vat - input_vat, decimal_places)

        vat_to_be_paid = (
            net_vat if net_vat > 0 else Decimal("0")
        ).quantize(Decimal("1").scaleb(-decimal_places))
        refund_due = (
            -net_vat if net_vat < 0 else Decimal("0")
        ).quantize(Decimal("1").scaleb(-decimal_places))

        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_to_be_paid": vat_to_be_paid,
            "refund_due": refund_due,
            "status": "payable" if vat_to_be_paid > 0 else "refund_or_zero",
        }

    return result
