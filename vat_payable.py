from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping

TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100")


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert a value to Decimal with clear validation errors."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """
    Accept VAT rates either as fractions (0.2) or percentages (20).

    A value greater than 1 is treated as percentage and divided by 100.
    """
    if rate < 0:
        raise ValueError("VAT rate cannot be negative")
    if rate > 1:
        return rate / HUNDRED
    return rate


def _money(amount: Decimal) -> Decimal:
    """Round to currency precision using standard half-up rounding."""
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Decimal]]:
    """
    Generate VAT totals and VAT payable for each jurisdiction.

    Expected transaction fields:
      - jurisdiction (str): Jurisdiction key (country/state/etc.)
      - type (str): Either "sale" (output VAT) or "purchase" (input VAT)
      - vat_amount (optional numeric): If present, this VAT amount is used directly
      - net_amount (numeric): Required when vat_amount is missing
      - vat_rate (numeric): Required when vat_amount is missing

    VAT payable formula per jurisdiction:
      vat_payable = output_vat - input_vat

    Returns:
      {
        "DE": {"output_vat": Decimal("20.00"), "input_vat": Decimal("5.00"), "vat_payable": Decimal("15.00")},
        ...
      }
    """
    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for index, transaction in enumerate(transactions):
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction at index {index} is missing 'jurisdiction'")

        tx_type = str(transaction.get("type", "")).strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction at index {index} has invalid 'type': {transaction.get('type')!r}"
            )

        if "vat_amount" in transaction and transaction["vat_amount"] is not None:
            vat_amount = _money(_to_decimal(transaction["vat_amount"], field_name="vat_amount"))
        else:
            if "net_amount" not in transaction:
                raise ValueError(f"Transaction at index {index} is missing 'net_amount'")
            if "vat_rate" not in transaction:
                raise ValueError(f"Transaction at index {index} is missing 'vat_rate'")

            net_amount = _to_decimal(transaction["net_amount"], field_name="net_amount")
            if net_amount < 0:
                raise ValueError("net_amount cannot be negative")

            rate = _normalize_rate(_to_decimal(transaction["vat_rate"], field_name="vat_rate"))
            vat_amount = _money(net_amount * rate)

        if tx_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: Dict[str, Dict[str, Decimal]] = {}
    for jurisdiction, values in totals.items():
        output_vat = _money(values["output_vat"])
        input_vat = _money(values["input_vat"])
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _money(output_vat - input_vat),
        }

    return result
