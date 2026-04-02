from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, Iterable, Literal, Union


NumberLike = Union[Decimal, int, float, str]
TransactionType = Literal["sale", "purchase"]


@dataclass(frozen=True)
class VATTransaction:
    jurisdiction: str
    taxable_amount: NumberLike
    vat_rate: NumberLike
    transaction_type: TransactionType


def _to_decimal(value: NumberLike, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {value!r}") from exc


def _normalize_rate(vat_rate: NumberLike) -> Decimal:
    rate = _to_decimal(vat_rate, "vat_rate")
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    # Accept either decimal rate (0.2) or percentage form (20)
    if rate > 1:
        rate = rate / Decimal("100")
    if rate > 1:
        raise ValueError("vat_rate cannot exceed 100%")
    return rate


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[VATTransaction],
) -> Dict[str, Dict[str, Decimal]]:
    """
    Generate VAT report per jurisdiction.

    Returns a dictionary with this shape:
    {
        "FR": {
            "output_vat": Decimal("120.00"),
            "input_vat": Decimal("30.00"),
            "net_vat": Decimal("90.00"),
            "vat_payable": Decimal("90.00"),
            "vat_credit": Decimal("0.00"),
        }
    }
    """

    output_totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    input_totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for tx in transactions:
        jurisdiction = tx.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("jurisdiction is required")

        taxable_amount = _to_decimal(tx.taxable_amount, "taxable_amount")
        if taxable_amount < 0:
            raise ValueError("taxable_amount cannot be negative")

        rate = _normalize_rate(tx.vat_rate)
        vat_amount = taxable_amount * rate

        if tx.transaction_type == "sale":
            output_totals[jurisdiction] += vat_amount
        elif tx.transaction_type == "purchase":
            input_totals[jurisdiction] += vat_amount
        else:
            raise ValueError(
                "transaction_type must be 'sale' or 'purchase', "
                f"got {tx.transaction_type!r}"
            )

    all_jurisdictions = set(output_totals) | set(input_totals)
    report: Dict[str, Dict[str, Decimal]] = {}

    for jurisdiction in sorted(all_jurisdictions):
        output_vat = _quantize_currency(output_totals[jurisdiction])
        input_vat = _quantize_currency(input_totals[jurisdiction])
        net_vat = _quantize_currency(output_vat - input_vat)
        vat_payable = _quantize_currency(max(net_vat, Decimal("0")))
        vat_credit = _quantize_currency(max(Decimal("0") - net_vat, Decimal("0")))

        report[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": vat_payable,
            "vat_credit": vat_credit,
        }

    return report
