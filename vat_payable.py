"""Compute VAT payable per jurisdiction.

This module provides:
1) `generate_vat_payable_by_jurisdiction` for in-memory transaction data.
2) A small CLI for CSV input/output reporting.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import argparse
import csv
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Summarized VAT values for a single jurisdiction."""

    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    vat_payable: Decimal
    vat_credit: Decimal


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"Invalid decimal in field '{field_name}': {value!r}") from exc


def _to_quantized(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _resolve_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    """Resolve VAT amount from either explicit vat_amount or amount * vat_rate."""
    if "vat_amount" in transaction and transaction["vat_amount"] not in (None, ""):
        return _to_decimal(transaction["vat_amount"], "vat_amount")

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction must include either 'vat_amount' or both "
            "'amount' and 'vat_rate'."
        )

    amount = _to_decimal(transaction["amount"], "amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    return amount * vat_rate


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, JurisdictionVatSummary]:
    """Generate VAT payable results grouped by jurisdiction.

    Expected transaction fields:
    - jurisdiction (required)
    - transaction_type (required): sale/output or purchase/input
    - vat_amount (optional, explicit VAT amount)
    - amount + vat_rate (optional alternative to vat_amount)
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Transaction is missing required field 'jurisdiction'.")

        transaction_type = str(transaction.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "output", "purchase", "input"}:
            raise ValueError(
                "transaction_type must be one of: sale, output, purchase, input."
            )

        vat_amount = _resolve_vat_amount(transaction)

        if transaction_type in {"sale", "output"}:
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, JurisdictionVatSummary] = {}
    for jurisdiction, values in totals.items():
        output_vat = _to_quantized(values["output_vat"])
        input_vat = _to_quantized(values["input_vat"])
        net_vat = _to_quantized(output_vat - input_vat)
        vat_payable = _to_quantized(max(net_vat, Decimal("0")))
        vat_credit = _to_quantized(max(-net_vat, Decimal("0")))

        result[jurisdiction] = JurisdictionVatSummary(
            jurisdiction=jurisdiction,
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            vat_payable=vat_payable,
            vat_credit=vat_credit,
        )

    return dict(sorted(result.items(), key=lambda item: item[0].lower()))


def _read_transactions_csv(input_path: str) -> list[dict[str, str]]:
    with open(input_path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _write_summary_csv(
    output_path: str, summaries: Mapping[str, JurisdictionVatSummary]
) -> None:
    fieldnames = [
        "jurisdiction",
        "output_vat",
        "input_vat",
        "net_vat",
        "vat_payable",
        "vat_credit",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries.values():
            writer.writerow(
                {
                    "jurisdiction": summary.jurisdiction,
                    "output_vat": f"{summary.output_vat:.2f}",
                    "input_vat": f"{summary.input_vat:.2f}",
                    "net_vat": f"{summary.net_vat:.2f}",
                    "vat_payable": f"{summary.vat_payable:.2f}",
                    "vat_credit": f"{summary.vat_credit:.2f}",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction CSV."
    )
    parser.add_argument("input_csv", help="Input transactions CSV path")
    parser.add_argument("output_csv", help="Output summary CSV path")
    args = parser.parse_args()

    transactions = _read_transactions_csv(args.input_csv)
    summaries = generate_vat_payable_by_jurisdiction(transactions)
    _write_summary_csv(args.output_csv, summaries)


if __name__ == "__main__":
    main()
