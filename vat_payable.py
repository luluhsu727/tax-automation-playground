"""Compute VAT payable per jurisdiction.

The core rule used here is:
    VAT payable = max(output VAT - input VAT, 0)

Input rows can provide either:
1) vat_amount directly, or
2) net_amount and vat_rate (rate can be decimal, e.g. 0.2, or percent, e.g. 20).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping


OUTPUT_TYPES = {"sale", "output", "collected"}
INPUT_TYPES = {"purchase", "input", "deductible"}


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid {field_name!r} value: {value!r}") from exc


def _normalize_vat_rate(raw_rate: object) -> Decimal:
    rate = _to_decimal(raw_rate, "vat_rate")
    # Accept either decimal rates (0.2) or percentage rates (20).
    if abs(rate) > Decimal("1"):
        rate = rate / Decimal("100")
    return rate


def _normalize_transaction_type(raw_type: object) -> str:
    tx_type = str(raw_type or "sale").strip().lower()
    if tx_type in OUTPUT_TYPES:
        return "output"
    if tx_type in INPUT_TYPES:
        return "input"
    raise ValueError(
        "Invalid transaction_type. Expected one of "
        f"{sorted(OUTPUT_TYPES | INPUT_TYPES)}, got {raw_type!r}"
    )


def _vat_amount_from_row(row: Mapping[str, object]) -> Decimal:
    vat_amount = row.get("vat_amount")
    if vat_amount not in (None, ""):
        amount = _to_decimal(vat_amount, "vat_amount")
        return abs(amount)

    net_amount = row.get("net_amount")
    vat_rate = row.get("vat_rate")
    if net_amount in (None, "") or vat_rate in (None, ""):
        raise ValueError(
            "Each row requires either 'vat_amount' or both 'net_amount' and 'vat_rate'."
        )

    net = _to_decimal(net_amount, "net_amount")
    rate = _normalize_vat_rate(vat_rate)
    return abs(net * rate)


def calculate_vat_payable_by_jurisdiction(
    rows: Iterable[Mapping[str, object]],
    *,
    currency_dp: int = 2,
) -> dict[str, Decimal]:
    """Aggregate VAT payable per jurisdiction.

    Args:
        rows: Iterable of row-like mappings. Required fields:
            - jurisdiction
            - transaction_type (sale/output or purchase/input), defaults to sale
            - vat_amount OR (net_amount + vat_rate)
        currency_dp: Number of decimal places for currency rounding.

    Returns:
        Mapping jurisdiction -> payable amount rounded to currency_dp.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    quant = Decimal("1").scaleb(-currency_dp)  # e.g. 0.01

    for idx, row in enumerate(rows, start=1):
        jurisdiction = str(row.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Row {idx}: missing jurisdiction")

        tx_type = _normalize_transaction_type(row.get("transaction_type", "sale"))
        vat_amount = _vat_amount_from_row(row)

        if tx_type == "output":
            totals[jurisdiction] += vat_amount
        else:
            totals[jurisdiction] -= vat_amount

    payable: dict[str, Decimal] = {}
    for jurisdiction in sorted(totals):
        amount_due = totals[jurisdiction]
        if amount_due < 0:
            amount_due = Decimal("0")
        payable[jurisdiction] = amount_due.quantize(quant, rounding=ROUND_HALF_UP)

    return payable


def load_rows_from_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _to_json_ready(result: Mapping[str, Decimal]) -> dict[str, str]:
    return {k: format(v, "f") for k, v in result.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount for each jurisdiction."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help=(
            "CSV path with columns including jurisdiction, transaction_type, and "
            "either vat_amount or (net_amount, vat_rate)."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format.",
    )
    args = parser.parse_args()

    rows = load_rows_from_csv(args.input_csv)
    result = calculate_vat_payable_by_jurisdiction(rows)

    if args.format == "json":
        print(json.dumps(_to_json_ready(result), indent=2, sort_keys=True))
        return

    writer = csv.writer(__import__("sys").stdout)
    writer.writerow(["jurisdiction", "vat_payable"])
    for jurisdiction, amount in result.items():
        writer.writerow([jurisdiction, format(amount, "f")])


if __name__ == "__main__":
    main()
