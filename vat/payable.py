from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Mapping


CENT = Decimal("0.01")


@dataclass(frozen=True)
class VATRecord:
    """A single VAT movement for a jurisdiction.

    output_vat is VAT collected on sales.
    input_vat is VAT paid on purchases that can be deducted.
    """

    jurisdiction: str
    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")


def calculate_vat_payable_by_jurisdiction(
    records: Iterable[VATRecord | Mapping[str, object]],
    *,
    clamp_negative: bool = False,
) -> dict[str, Decimal]:
    """Calculate net VAT payable for each jurisdiction.

    Net VAT payable = sum(output_vat) - sum(input_vat)

    A negative result means VAT is recoverable (credit/refund).
    Set clamp_negative=True to return 0.00 for those jurisdictions.
    """

    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for raw_record in records:
        record = _coerce_record(raw_record)
        net_vat = record.output_vat - record.input_vat
        totals[record.jurisdiction] += net_vat

    result: dict[str, Decimal] = {}
    for jurisdiction, amount in totals.items():
        normalized = _to_decimal(amount)
        if clamp_negative and normalized < 0:
            normalized = Decimal("0")
        result[jurisdiction] = normalized
    return result


def _coerce_record(record: VATRecord | Mapping[str, object]) -> VATRecord:
    if isinstance(record, VATRecord):
        return VATRecord(
            jurisdiction=record.jurisdiction,
            output_vat=_to_decimal(record.output_vat),
            input_vat=_to_decimal(record.input_vat),
        )

    jurisdiction = str(record["jurisdiction"]).strip()
    if not jurisdiction:
        raise ValueError("jurisdiction must be a non-empty string")

    output_vat = _to_decimal(record.get("output_vat", 0))
    input_vat = _to_decimal(record.get("input_vat", 0))
    return VATRecord(
        jurisdiction=jurisdiction,
        output_vat=output_vat,
        input_vat=input_vat,
    )


def _to_decimal(value: object) -> Decimal:
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid VAT amount: {value!r}") from exc
    return converted.quantize(CENT, rounding=ROUND_HALF_UP)
