"""Utilities for generating VAT payable amounts by jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, MutableMapping

_SALES_TYPES = {"sale", "sales", "output"}
_PURCHASE_TYPES = {"purchase", "purchases", "input"}


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _quantize(amount: Decimal, places: int) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return amount.quantize(quantizer, rounding=ROUND_HALF_UP)


def _normalize_transaction_type(raw_type: object) -> str:
    transaction_type = str(raw_type).strip().lower()
    if transaction_type in _SALES_TYPES:
        return "sale"
    if transaction_type in _PURCHASE_TYPES:
        return "purchase"
    raise ValueError(
        "Transaction type must be one of "
        f"{sorted(_SALES_TYPES | _PURCHASE_TYPES)}; got {raw_type!r}"
    )


def _compute_vat_amount(transaction: Mapping[str, object]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        if vat_amount < 0:
            raise ValueError("vat_amount cannot be negative")
        return vat_amount

    if "net_amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError("Transaction must include vat_amount OR both net_amount and vat_rate")

    net_amount = _to_decimal(transaction["net_amount"], "net_amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    if net_amount < 0:
        raise ValueError("net_amount cannot be negative")
    if vat_rate < 0:
        raise ValueError("vat_rate cannot be negative")

    return net_amount * vat_rate


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
    rounding_places: int = 2,
) -> dict[str, dict[str, Decimal]]:
    """Generate output VAT, input VAT and VAT payable grouped by jurisdiction.

    A transaction must include:
      - jurisdiction: non-empty string
      - type: one of sale/sales/output or purchase/purchases/input
      - either vat_amount OR (net_amount and vat_rate)

    Returns a mapping:
      {
        "<jurisdiction>": {
          "output_vat": Decimal,
          "input_vat": Decimal,
          "vat_payable": Decimal
        }
      }
    """

    if rounding_places < 0:
        raise ValueError("rounding_places cannot be negative")

    aggregates: MutableMapping[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Transaction must include a non-empty jurisdiction")

        transaction_type = _normalize_transaction_type(transaction.get("type", ""))
        vat_amount = _compute_vat_amount(transaction)

        if transaction_type == "sale":
            aggregates[jurisdiction]["output_vat"] += vat_amount
        else:
            aggregates[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, totals in aggregates.items():
        output_vat = _quantize(totals["output_vat"], rounding_places)
        input_vat = _quantize(totals["input_vat"], rounding_places)
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _quantize(output_vat - input_vat, rounding_places),
        }

    return result
