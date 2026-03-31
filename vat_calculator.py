from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(vat_rate: Any) -> Decimal:
    rate = _to_decimal(vat_rate, "vat_rate")
    # Accept either decimal form (0.2) or percentage form (20).
    if rate > Decimal("1"):
        rate = rate / Decimal("100")
    if rate < Decimal("0"):
        raise ValueError("vat_rate cannot be negative")
    return rate


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _compute_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat = _to_decimal(transaction["vat_amount"], "vat_amount")
        if vat < Decimal("0"):
            raise ValueError("vat_amount cannot be negative")
        return _round_money(vat)

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Transaction must include either 'vat_amount' or both 'amount' and 'vat_rate'"
        )

    amount = _to_decimal(transaction["amount"], "amount")
    if amount < Decimal("0"):
        raise ValueError("amount cannot be negative")

    rate = _normalize_rate(transaction["vat_rate"])
    vat = amount * rate
    return _round_money(vat)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Decimal]]:
    """
    Aggregate transactions and compute VAT position for each jurisdiction.

    Returns a mapping keyed by jurisdiction with:
    - output_vat
    - input_vat
    - net_vat
    - vat_payable
    - vat_reclaimable
    """
    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            raise ValueError("Each transaction must be a mapping")

        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError("Each transaction must have a non-empty 'jurisdiction'")
        jurisdiction = jurisdiction.strip()

        transaction_type = transaction.get("type")
        if not isinstance(transaction_type, str):
            raise ValueError("Each transaction must include a 'type' of 'sale' or 'purchase'")
        transaction_type = transaction_type.lower().strip()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError("type must be either 'sale' or 'purchase'")

        vat_amount = _compute_vat_amount(transaction)
        if transaction_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    results: Dict[str, Dict[str, Decimal]] = {}
    for jurisdiction, values in totals.items():
        output_vat = _round_money(values["output_vat"])
        input_vat = _round_money(values["input_vat"])
        net_vat = _round_money(output_vat - input_vat)
        vat_payable = _round_money(max(net_vat, Decimal("0")))
        vat_reclaimable = _round_money(max(-net_vat, Decimal("0")))

        results[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": vat_payable,
            "vat_reclaimable": vat_reclaimable,
        }

    return results
