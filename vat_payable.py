#!/usr/bin/env python3
"""Generate VAT payable amounts by jurisdiction."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid numeric value for '{field_name}': {value}") from exc


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build jurisdiction-level VAT summary and payable amounts.

    Expected transaction fields:
    - jurisdiction (required): string key for country/region/state
    - output_vat (optional): VAT collected on sales
    - input_vat (optional): VAT paid on purchases
    - taxable_amount (optional): if output_vat absent, used with vat_rate
    - vat_rate (optional): decimal rate (e.g. 0.19)
    """
    per_jurisdiction: dict[str, dict[str, Decimal]] = {}

    for idx, txn in enumerate(transactions):
        jurisdiction = txn.get("jurisdiction")
        if not jurisdiction:
            raise ValueError(
                f"Transaction at index {idx} is missing required 'jurisdiction'."
            )

        if jurisdiction not in per_jurisdiction:
            per_jurisdiction[jurisdiction] = {
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
            }

        if txn.get("output_vat") is not None:
            output_vat = _to_decimal(txn.get("output_vat"), "output_vat")
        else:
            taxable_amount = _to_decimal(txn.get("taxable_amount"), "taxable_amount")
            vat_rate = _to_decimal(txn.get("vat_rate"), "vat_rate")
            output_vat = taxable_amount * vat_rate

        input_vat = _to_decimal(txn.get("input_vat"), "input_vat")

        per_jurisdiction[jurisdiction]["output_vat"] += output_vat
        per_jurisdiction[jurisdiction]["input_vat"] += input_vat

    jurisdictions: list[dict[str, Any]] = []
    total_output = Decimal("0")
    total_input = Decimal("0")
    total_payable = Decimal("0")
    total_credit = Decimal("0")

    for jurisdiction in sorted(per_jurisdiction):
        output_vat = _quantize(per_jurisdiction[jurisdiction]["output_vat"])
        input_vat = _quantize(per_jurisdiction[jurisdiction]["input_vat"])
        net_vat = _quantize(output_vat - input_vat)
        vat_payable = _quantize(max(net_vat, Decimal("0")))
        vat_credit = _quantize(max(-net_vat, Decimal("0")))

        jurisdictions.append(
            {
                "jurisdiction": jurisdiction,
                "output_vat": str(output_vat),
                "input_vat": str(input_vat),
                "net_vat": str(net_vat),
                "vat_payable": str(vat_payable),
                "vat_credit": str(vat_credit),
            }
        )

        total_output += output_vat
        total_input += input_vat
        total_payable += vat_payable
        total_credit += vat_credit

    total_net = _quantize(total_output - total_input)

    return {
        "jurisdictions": jurisdictions,
        "totals": {
            "output_vat": str(_quantize(total_output)),
            "input_vat": str(_quantize(total_input)),
            "net_vat": str(total_net),
            "vat_payable": str(_quantize(total_payable)),
            "vat_credit": str(_quantize(total_credit)),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction from transactions."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON file containing a list of transactions.",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Optional output JSON path. Prints to stdout when omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input)
    transactions = json.loads(input_path.read_text(encoding="utf-8"))
    result = generate_vat_payable_by_jurisdiction(transactions)
    result_json = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(result_json + "\n", encoding="utf-8")
    else:
        print(result_json)


if __name__ == "__main__":
    main()
