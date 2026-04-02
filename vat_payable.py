#!/usr/bin/env python3
"""Compute VAT payable per jurisdiction from transaction records."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping

TWO_DP = Decimal("0.01")
DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


def _to_decimal(value: object, field_name: str = "value") -> Decimal:
    """Convert supported input values to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        raise ValueError(f"Missing required numeric field: {field_name}")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for {field_name}: {value}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Accept decimal rates (0.19) or percentage rates (19)."""
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _round_currency(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction record."""

    jurisdiction: str
    transaction_type: str
    amount: Decimal
    vat_rate: Decimal

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "Transaction":
        jurisdiction = str(item["jurisdiction"]).strip().upper()
        transaction_type = str(item["type"]).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        amount = _to_decimal(item.get("amount"), "amount")
        vat_rate = _normalize_rate(_to_decimal(item.get("vat_rate"), "vat_rate"))

        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if vat_rate < 0:
            raise ValueError("VAT rate cannot be negative")
        if not jurisdiction:
            raise ValueError("Jurisdiction cannot be empty")

        return cls(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            amount=amount,
            vat_rate=vat_rate,
        )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Calculate VAT payable details for each jurisdiction.

    Returns a dictionary keyed by jurisdiction with:
      - output_vat: VAT collected on sales
      - input_vat: VAT paid on purchases
      - vat_payable: output_vat - input_vat
    """
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
        if tx.transaction_type == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: Dict[str, Dict[str, float]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _round_currency(totals[jurisdiction]["output_vat"])
        input_vat = _round_currency(totals[jurisdiction]["input_vat"])
        vat_payable = _round_currency(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }
    return result


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Compatibility alias for callers using the compute_* naming."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, float]:
    """
    Return VAT-to-be-paid totals keyed by jurisdiction.

    Supports two transaction schemas:
      1) {"jurisdiction", "type", "amount", "vat_rate"}
      2) {"jurisdiction", "taxable_amount"|"amount", optional "vat_rate"}
    """
    cached_transactions = list(transactions)
    if not cached_transactions:
        return {}

    first = cached_transactions[0]
    if "type" in first:
        vat_summary = calculate_vat_payable_by_jurisdiction(cached_transactions)
        return {
            jurisdiction: values["vat_payable"]
            for jurisdiction, values in vat_summary.items()
        }

    totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for item in cached_transactions:
        jurisdiction = str(item.get("jurisdiction", "")).strip().upper()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty jurisdiction.")

        amount_raw = item.get("taxable_amount", item.get("amount"))
        taxable_amount = _to_decimal(amount_raw, "taxable_amount")
        raw_rate = item.get("vat_rate")
        if raw_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(
                    f"No VAT rate supplied for jurisdiction '{jurisdiction}', "
                    "and no default rate is configured."
                )
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]
        else:
            vat_rate = _normalize_rate(_to_decimal(raw_rate, "vat_rate"))

        totals[jurisdiction] += _round_currency(taxable_amount * vat_rate)

    return {
        jurisdiction: float(_round_currency(vat_amount))
        for jurisdiction, vat_amount in sorted(totals.items())
    }


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
        for jurisdiction, amounts in vat_data.items():
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
