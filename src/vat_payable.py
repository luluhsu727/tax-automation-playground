from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


def _to_decimal(value: Any) -> Decimal:
    """Convert supported numeric input to Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise TypeError(f"Unsupported numeric value: {value!r}")


def _normalize_money(value: Decimal) -> Decimal:
    """Round to cents with standard half-up rounding."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _rate_to_fraction(value: Any) -> Decimal:
    """
    Normalize VAT rate to a fraction.

    Accepts either:
      - decimal fraction (e.g. 0.2 for 20%)
      - whole percent (e.g. 20 for 20%)
    """
    rate = _to_decimal(value)
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _compute_output_vat(record: dict[str, Any]) -> Decimal:
    if "output_vat" in record:
        return _to_decimal(record["output_vat"])

    sales_amount = _to_decimal(record.get("sales_amount", 0))
    vat_rate = _rate_to_fraction(record.get("vat_rate", 0))
    return sales_amount * vat_rate


def _compute_input_vat(record: dict[str, Any]) -> Decimal:
    if "input_vat" in record:
        return _to_decimal(record["input_vat"])

    purchase_amount = _to_decimal(record.get("purchase_amount", 0))
    deductible_vat_rate = _rate_to_fraction(record.get("deductible_vat_rate", 0))
    return purchase_amount * deductible_vat_rate


def vat_payable_by_jurisdiction(records: list[dict[str, Any]]) -> dict[str, float]:
    """
    Generate VAT payable for each jurisdiction.

    Each record must include:
      - jurisdiction (string)
    And can include one of:
      - output_vat and input_vat
      - sales_amount and vat_rate (+ optional purchase_amount and deductible_vat_rate)
    """
    output_totals: dict[str, Decimal] = {}
    input_totals: dict[str, Decimal] = {}

    for record in records:
        jurisdiction = record.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(f"Invalid jurisdiction in record: {record!r}")

        output_vat = _compute_output_vat(record)
        input_vat = _compute_input_vat(record)
        output_totals[jurisdiction] = (
            output_totals.get(jurisdiction, Decimal("0")) + output_vat
        )
        input_totals[jurisdiction] = (
            input_totals.get(jurisdiction, Decimal("0")) + input_vat
        )

    jurisdictions = set(output_totals) | set(input_totals)
    totals: dict[str, float] = {}
    for jurisdiction in sorted(jurisdictions):
        payable = output_totals.get(jurisdiction, Decimal("0")) - input_totals.get(
            jurisdiction, Decimal("0")
        )
        # "VAT to be paid" is never negative; negative net VAT is reclaimable.
        payable = max(payable, Decimal("0"))
        totals[jurisdiction] = float(_normalize_money(payable))

    return totals


def _load_records(input_file: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of records.")

    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Record at index {idx} must be an object.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount for each jurisdiction."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input JSON file with jurisdiction VAT records.",
    )
    args = parser.parse_args()

    records = _load_records(args.input_file)
    result = vat_payable_by_jurisdiction(records)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
