"""Minimal src-style API for VAT payable calculations.

Several historical tests import ``src.vat_payable``. This module keeps that
surface available and delegates to common Decimal-safe logic.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from vat_core import money, normalize_jurisdiction, to_decimal, to_rate


def _derived_output_vat(record: dict[str, Any]) -> Decimal:
    if record.get("output_vat") is not None:
        return to_decimal(record.get("output_vat"), field_name="output_vat")
    sales_amount = to_decimal(record.get("sales_amount", 0), field_name="sales_amount")
    vat_rate = to_rate(record.get("vat_rate", 0), field_name="vat_rate")
    return sales_amount * vat_rate


def _derived_input_vat(record: dict[str, Any]) -> Decimal:
    if record.get("input_vat") is not None:
        return to_decimal(record.get("input_vat"), field_name="input_vat")
    purchase_amount = to_decimal(
        record.get("purchase_amount", 0), field_name="purchase_amount"
    )
    deductible_rate = to_rate(
        record.get("deductible_vat_rate", record.get("vat_rate", 0)),
        field_name="deductible_vat_rate",
    )
    return purchase_amount * deductible_rate


def vat_payable_by_jurisdiction(records: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, Decimal] = {}
    for record in records:
        jurisdiction = normalize_jurisdiction(record.get("jurisdiction"))
        output_vat = money(_derived_output_vat(record))
        input_vat = money(_derived_input_vat(record))
        net = money(output_vat - input_vat)
        payable = money(net if net > 0 else Decimal("0.00"))
        totals[jurisdiction] = money(totals.get(jurisdiction, Decimal("0.00")) + payable)
    return {j: float(v) for j, v in sorted(totals.items())}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to input JSON records file")
    args = parser.parse_args()

    records = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
    result = vat_payable_by_jurisdiction(records)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
