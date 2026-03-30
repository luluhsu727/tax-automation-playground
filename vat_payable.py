#!/usr/bin/env python3
"""Generate VAT payable totals for each jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Mapping

TWO_DP = Decimal("0.01")
SALE = "sale"
PURCHASE = "purchase"
VALID_TYPES = {SALE, PURCHASE}


def _to_decimal(value: object, *, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion error
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    amount: Decimal
    vat_rate: Decimal

    @classmethod
    def from_mapping(cls, item: Mapping[str, object]) -> "Transaction":
        jurisdiction = str(item["jurisdiction"]).strip().upper()
        transaction_type = str(item["type"]).strip().lower()

        if not jurisdiction:
            raise ValueError("Jurisdiction cannot be empty")
        if transaction_type not in VALID_TYPES:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        amount = _to_decimal(item["amount"], field_name="amount")
        vat_rate = _to_decimal(item["vat_rate"], field_name="vat_rate")

        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if vat_rate < 0:
            raise ValueError("VAT rate cannot be negative")

        # Accept percentage-style rates (e.g. 19 for 19%).
        if vat_rate > 1:
            vat_rate = vat_rate / Decimal("100")

        return cls(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            amount=amount,
            vat_rate=vat_rate,
        )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, Dict[str, float]]:
    """Return output VAT, input VAT, and net VAT payable by jurisdiction."""
    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for raw in transactions:
        tx = Transaction.from_mapping(raw)
        vat_amount = tx.amount * tx.vat_rate
        bucket = totals[tx.jurisdiction]
        if tx.transaction_type == SALE:
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: Dict[str, Dict[str, float]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _to_money(totals[jurisdiction]["output_vat"])
        input_vat = _to_money(totals[jurisdiction]["input_vat"])
        vat_payable = _to_money(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }
    return result


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, float]:
    """Return non-negative VAT payable amounts keyed by jurisdiction."""
    detailed = calculate_vat_payable_by_jurisdiction(transactions)
    return {
        jurisdiction: max(0.0, amounts["vat_payable"])
        for jurisdiction, amounts in detailed.items()
    }


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, float]:
    """Compatibility alias for common task wording."""
    return generate_vat_to_be_paid_by_jurisdiction(transactions)


def _read_transactions_json(path: str) -> list[dict[str, object]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transactions")
    return payload


def _write_csv_report(path: str, vat_data: Dict[str, Dict[str, float]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jurisdiction", "output_vat", "input_vat", "vat_payable"])
        for jurisdiction in sorted(vat_data):
            amounts = vat_data[jurisdiction]
            writer.writerow(
                [
                    jurisdiction,
                    f"{amounts['output_vat']:.2f}",
                    f"{amounts['input_vat']:.2f}",
                    f"{amounts['vat_payable']:.2f}",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable report for each jurisdiction."
    )
    parser.add_argument("input_json", help="Path to input transactions JSON file")
    parser.add_argument(
        "--output-csv",
        default="vat_payable_by_jurisdiction.csv",
        help="CSV file path for VAT payable report",
    )
    args = parser.parse_args()

    transactions = _read_transactions_json(args.input_json)
    vat_data = calculate_vat_payable_by_jurisdiction(transactions)
    _write_csv_report(args.output_csv, vat_data)
    print(json.dumps(vat_data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
