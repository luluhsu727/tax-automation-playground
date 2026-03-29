"""Generate VAT payable amounts per jurisdiction.

This module supports both direct Python usage and CLI execution over CSV files.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Aggregated VAT values for a jurisdiction."""

    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")

    @property
    def vat_payable(self) -> Decimal:
        return self.output_vat - self.input_vat


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None or value == "":
        raise ValueError(f"'{field_name}' cannot be empty")

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(raw_rate: Any) -> Decimal:
    """Normalize VAT rate to decimal fraction.

    Examples:
      - 0.2 -> 0.2
      - 20 -> 0.2
      - "7.5" -> 0.075
    """
    rate = _to_decimal(raw_rate, "vat_rate")
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


def _round_currency(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _get_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    vat_amount = transaction.get("vat_amount")
    if vat_amount not in (None, ""):
        return _round_currency(_to_decimal(vat_amount, "vat_amount"))

    taxable_amount = _to_decimal(transaction.get("taxable_amount"), "taxable_amount")
    vat_rate = _normalize_rate(transaction.get("vat_rate"))
    return _round_currency(taxable_amount * vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, JurisdictionVatSummary]:
    """Compute output/input VAT and payable VAT by jurisdiction.

    Required fields per transaction:
      - jurisdiction: str
      - transaction_type: 'sale' or 'purchase'
      - vat_amount OR (taxable_amount and vat_rate)
    """
    output_vat_by_jurisdiction: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    input_vat_by_jurisdiction: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for idx, transaction in enumerate(transactions, start=1):
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction #{idx} is missing 'jurisdiction'")

        transaction_type = str(transaction.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction #{idx} has invalid 'transaction_type': {transaction_type!r}. "
                "Expected 'sale' or 'purchase'."
            )

        vat = _get_vat_amount(transaction)

        if transaction_type == "sale":
            output_vat_by_jurisdiction[jurisdiction] += vat
        else:
            input_vat_by_jurisdiction[jurisdiction] += vat

    jurisdictions = sorted(set(output_vat_by_jurisdiction) | set(input_vat_by_jurisdiction))
    result: dict[str, JurisdictionVatSummary] = {}
    for jurisdiction in jurisdictions:
        result[jurisdiction] = JurisdictionVatSummary(
            output_vat=_round_currency(output_vat_by_jurisdiction[jurisdiction]),
            input_vat=_round_currency(input_vat_by_jurisdiction[jurisdiction]),
        )
    return result


def load_transactions_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("Input CSV is missing a header row")
        return [dict(row) for row in reader]


def write_vat_summary_csv(path: str | Path, report: Mapping[str, JurisdictionVatSummary]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["jurisdiction", "output_vat", "input_vat", "vat_payable"],
        )
        writer.writeheader()
        for jurisdiction in sorted(report):
            summary = report[jurisdiction]
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "output_vat": f"{summary.output_vat:.2f}",
                    "input_vat": f"{summary.input_vat:.2f}",
                    "vat_payable": f"{summary.vat_payable:.2f}",
                }
            )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amounts for each jurisdiction from transactions CSV."
    )
    parser.add_argument(
        "input_csv",
        help="Path to input CSV with fields: jurisdiction, transaction_type, taxable_amount, vat_rate, vat_amount",
    )
    parser.add_argument(
        "--output-csv",
        default="vat_payable_report.csv",
        help="Path to write VAT summary CSV (default: vat_payable_report.csv)",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    transactions = load_transactions_csv(args.input_csv)
    report = generate_vat_payable_by_jurisdiction(transactions)
    write_vat_summary_csv(args.output_csv, report)
    print(f"Wrote VAT payable report to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
