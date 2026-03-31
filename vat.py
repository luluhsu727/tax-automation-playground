"""Utilities for generating VAT payable per jurisdiction."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

DEFAULT_AMOUNT_KEYS = ("amount", "taxable_amount", "net_amount")
DEFAULT_RATE_KEYS = ("vat_rate", "rate", "vat_percentage")


def _to_decimal(value: Any) -> Decimal:
    """Convert numeric-like values to Decimal."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Unable to parse numeric value: {value!r}") from exc


def _extract_value(
    record: Mapping[str, Any],
    *,
    record_index: int,
    explicit_key: str | None,
    candidate_keys: tuple[str, ...],
    field_label: str,
) -> Any:
    if explicit_key is not None:
        if explicit_key not in record:
            raise ValueError(
                f"Record {record_index} is missing required key {explicit_key!r} for {field_label}."
            )
        return record[explicit_key]

    for key in candidate_keys:
        if key in record:
            return record[key]

    raise ValueError(
        f"Record {record_index} does not include any supported {field_label} keys: "
        f"{', '.join(candidate_keys)}."
    )


def _normalize_rate(rate_value: Any, rates_are_percentages: bool | None) -> Decimal:
    """Normalize VAT rates to decimal fractions."""
    rate = _to_decimal(rate_value)
    if rates_are_percentages is True:
        return rate / Decimal("100")
    if rates_are_percentages is False:
        return rate
    if abs(rate) > Decimal("1"):
        return rate / Decimal("100")
    return rate


def calculate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    jurisdiction_key: str = "jurisdiction",
    amount_key: str | None = None,
    vat_rate_key: str | None = None,
    rates_are_percentages: bool | None = None,
    rounding_places: int = 2,
) -> dict[str, Decimal]:
    """
    Calculate VAT totals grouped by jurisdiction.

    Returns a mapping from jurisdiction to VAT amount rounded half-up to
    ``rounding_places`` decimals.
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)

    for index, record in enumerate(transactions):
        if not isinstance(record, Mapping):
            raise ValueError(f"Record {index} is not a mapping: {record!r}")

        if jurisdiction_key not in record:
            raise ValueError(
                f"Record {index} is missing required key {jurisdiction_key!r}."
            )

        jurisdiction = str(record[jurisdiction_key]).strip()
        if not jurisdiction:
            raise ValueError(f"Record {index} has an empty jurisdiction value.")

        amount = _to_decimal(
            _extract_value(
                record,
                record_index=index,
                explicit_key=amount_key,
                candidate_keys=DEFAULT_AMOUNT_KEYS,
                field_label="amount",
            )
        )
        rate = _normalize_rate(
            _extract_value(
                record,
                record_index=index,
                explicit_key=vat_rate_key,
                candidate_keys=DEFAULT_RATE_KEYS,
                field_label="VAT rate",
            ),
            rates_are_percentages,
        )

        totals[jurisdiction] += amount * rate

    quantize_target = Decimal("1").scaleb(-rounding_places)
    return {
        jurisdiction: total.quantize(quantize_target, rounding=ROUND_HALF_UP)
        for jurisdiction, total in totals.items()
    }


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]], **kwargs: Any
) -> dict[str, Decimal]:
    """Alias for calculate_vat_to_be_paid_by_jurisdiction."""
    return calculate_vat_to_be_paid_by_jurisdiction(transactions, **kwargs)


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]], **kwargs: Any
) -> dict[str, Decimal]:
    """Alias for calculate_vat_to_be_paid_by_jurisdiction."""
    return calculate_vat_to_be_paid_by_jurisdiction(transactions, **kwargs)
