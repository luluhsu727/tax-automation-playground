from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Mapping


ZERO = Decimal("0")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class JurisdictionVATSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    payable_vat: Decimal
    reclaimable_vat: Decimal


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_vat_rate(rate: Any) -> Decimal:
    parsed = _to_decimal(rate, "vat_rate")
    if parsed < ZERO:
        raise ValueError(f"vat_rate cannot be negative: {rate!r}")
    if parsed > Decimal("1"):
        parsed = parsed / HUNDRED
    return parsed


def _transaction_vat_amount(record: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in record and record["vat_amount"] not in (None, ""):
        amount = _to_decimal(record["vat_amount"], "vat_amount")
        if amount < ZERO:
            raise ValueError(f"vat_amount cannot be negative: {record['vat_amount']!r}")
        return amount

    base_amount = _to_decimal(record["amount"], "amount")
    if base_amount < ZERO:
        raise ValueError(f"amount cannot be negative: {record['amount']!r}")

    vat_rate = _normalize_vat_rate(record["vat_rate"])
    return base_amount * vat_rate


def calculate_vat_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, JurisdictionVATSummary]:
    """
    Calculate VAT summary per jurisdiction.

    Required fields per transaction:
    - jurisdiction: str
    - transaction_type: "sale" or "purchase"
    - Either:
        - vat_amount
      or
        - amount and vat_rate
    """
    ledger: Dict[str, Dict[str, Decimal]] = {}

    for record in transactions:
        jurisdiction = str(record.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction must include a jurisdiction.")

        transaction_type = str(record.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type {transaction_type!r} "
                f"for jurisdiction {jurisdiction!r}. Use 'sale' or 'purchase'."
            )

        vat_value = _transaction_vat_amount(record)
        if jurisdiction not in ledger:
            ledger[jurisdiction] = {"output_vat": ZERO, "input_vat": ZERO}

        if transaction_type == "sale":
            ledger[jurisdiction]["output_vat"] += vat_value
        else:
            ledger[jurisdiction]["input_vat"] += vat_value

    summary: Dict[str, JurisdictionVATSummary] = {}
    for jurisdiction, values in ledger.items():
        output_vat = values["output_vat"]
        input_vat = values["input_vat"]
        net_vat = output_vat - input_vat
        payable_vat = net_vat if net_vat > ZERO else ZERO
        reclaimable_vat = -net_vat if net_vat < ZERO else ZERO

        summary[jurisdiction] = JurisdictionVATSummary(
            jurisdiction=jurisdiction,
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            payable_vat=payable_vat,
            reclaimable_vat=reclaimable_vat,
        )

    return summary


def vat_to_be_paid_per_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Decimal]:
    """
    Return payable VAT per jurisdiction.

    This returns only VAT that must be paid (never negative values).
    """
    summary = calculate_vat_by_jurisdiction(transactions)
    return {jurisdiction: row.payable_vat for jurisdiction, row in summary.items()}


def serialize_summary(summary: Mapping[str, JurisdictionVATSummary]) -> List[Dict[str, str]]:
    """
    Serialize a VAT summary into JSON-friendly dictionaries.

    Decimal values are converted to strings to preserve precision.
    """
    return [
        {
            "jurisdiction": row.jurisdiction,
            "output_vat": str(row.output_vat),
            "input_vat": str(row.input_vat),
            "net_vat": str(row.net_vat),
            "payable_vat": str(row.payable_vat),
            "reclaimable_vat": str(row.reclaimable_vat),
        }
        for row in summary.values()
    ]
