"""Core VAT payable calculations by jurisdiction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert int/float/str/Decimal values safely to Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric, got bool")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"Invalid numeric value for {field_name}: {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """
    Normalize VAT rates:
    - 0.20 stays 0.20
    - 20 becomes 0.20
    """
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _quantize(value: Decimal, precision: Decimal = TWOPLACES) -> Decimal:
    return value.quantize(precision, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class JurisdictionVATResult:
    """Aggregated VAT values for a single jurisdiction."""

    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    vat_payable: Decimal

    def to_dict(self) -> dict[str, str]:
        return {
            "output_vat": format(self.output_vat, "f"),
            "input_vat": format(self.input_vat, "f"),
            "net_vat": format(self.net_vat, "f"),
            "vat_payable": format(self.vat_payable, "f"),
        }


def _resolve_vat_amount(transaction: dict[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], field_name="vat_amount")
        if vat_amount < 0:
            raise ValueError("vat_amount cannot be negative")
        return vat_amount

    if "net_amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError("Each transaction requires vat_amount or (net_amount and vat_rate)")

    net_amount = _to_decimal(transaction["net_amount"], field_name="net_amount")
    vat_rate = _normalize_rate(_to_decimal(transaction["vat_rate"], field_name="vat_rate"))
    if net_amount < 0:
        raise ValueError("net_amount cannot be negative")
    return net_amount * vat_rate


def _resolve_direction(transaction: dict[str, Any]) -> str:
    transaction_type = str(transaction.get("transaction_type", "")).strip().lower()
    mapping = {
        "sale": "output",
        "sales": "output",
        "output": "output",
        "purchase": "input",
        "purchases": "input",
        "input": "input",
    }
    if transaction_type not in mapping:
        raise ValueError(
            "transaction_type must be one of: sale, sales, output, purchase, purchases, input"
        )
    return mapping[transaction_type]


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
    *,
    precision: Decimal = TWOPLACES,
) -> dict[str, JurisdictionVATResult]:
    """
    Calculate VAT payable by jurisdiction.

    Each transaction must include:
      - jurisdiction: str
      - transaction_type: sale/output or purchase/input
      - vat_amount OR (net_amount and vat_rate)
    """
    aggregates: dict[str, dict[str, Decimal]] = {}

    for tx in transactions:
        jurisdiction = str(tx.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("jurisdiction is required for each transaction")

        direction = _resolve_direction(tx)
        vat_amount = _resolve_vat_amount(tx)

        if jurisdiction not in aggregates:
            aggregates[jurisdiction] = {"output_vat": Decimal("0"), "input_vat": Decimal("0")}

        if direction == "output":
            aggregates[jurisdiction]["output_vat"] += vat_amount
        else:
            aggregates[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, JurisdictionVATResult] = {}
    for jurisdiction, values in aggregates.items():
        output_vat = _quantize(values["output_vat"], precision)
        input_vat = _quantize(values["input_vat"], precision)
        net_vat = _quantize(output_vat - input_vat, precision)
        vat_payable = _quantize(max(net_vat, Decimal("0")), precision)
        result[jurisdiction] = JurisdictionVATResult(
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            vat_payable=vat_payable,
        )

    return result
