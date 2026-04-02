"""Generate VAT to be paid for each jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")

DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for '{field_name}': {raw_value}") from exc


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Aggregate VAT payable totals by jurisdiction."""
    totals: dict[str, dict[str, Decimal]] = {}

    for row in transactions:
        jurisdiction = str(row.get("jurisdiction", "")).strip().upper()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction.")

        taxable_amount = _parse_decimal(row.get("taxable_amount"), "taxable_amount")
        vat_rate_value = row.get("vat_rate")
        vat_rate = (
            _parse_decimal(vat_rate_value, "vat_rate") if vat_rate_value is not None else None
        )

        if vat_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(
                    f"No VAT rate supplied for jurisdiction '{jurisdiction}', "
                    "and no default rate is configured."
                )
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]
        elif vat_rate > 1:
            # Support percent-format input (e.g. 19 for 19%).
            vat_rate = vat_rate / Decimal("100")

        vat_payable = _money(taxable_amount * vat_rate)
        if jurisdiction not in totals:
            totals[jurisdiction] = {
                "total_taxable_amount": Decimal("0.00"),
                "total_vat_payable": Decimal("0.00"),
            }
        totals[jurisdiction]["total_taxable_amount"] += taxable_amount
        totals[jurisdiction]["total_vat_payable"] += vat_payable

    summary_rows: list[dict[str, str]] = []
    for jurisdiction in sorted(totals):
        taxable_total = _money(totals[jurisdiction]["total_taxable_amount"])
        payable_total = _money(totals[jurisdiction]["total_vat_payable"])
        effective_rate = (
            _money(payable_total / taxable_total)
            if taxable_total != Decimal("0.00")
            else Decimal("0.00")
        )
        summary_rows.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{payable_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )

    return summary_rows


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Return only the VAT-to-be-paid amount for each jurisdiction."""
    summary = compute_vat_payable_by_jurisdiction(transactions)
    return {row["jurisdiction"]: Decimal(row["total_vat_payable"]) for row in summary}


def generate_vat_to_be_paid_for_jurisdictions(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Backward-compatible alias with equivalent behavior."""
    return generate_vat_to_be_paid_for_each_jurisdiction(transactions)


__all__ = [
    "compute_vat_payable_by_jurisdiction",
    "generate_vat_to_be_paid_for_each_jurisdiction",
    "generate_vat_to_be_paid_for_jurisdictions",
]
