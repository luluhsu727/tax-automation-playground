"""Generate VAT payable per jurisdiction.

This module provides:
- A reusable function to calculate VAT payable by jurisdiction.
- A small CLI for generating a report from a CSV file.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

TWOPLACES = Decimal("0.01")


def _to_decimal(value: object, field_name: str) -> Decimal:
    """Convert an input value into Decimal with clear errors."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: object, field_name: str = "vat_rate") -> Decimal:
    """Normalize VAT rate to a 0..1 decimal.

    Accepts either a fraction (0.2 for 20%) or a percent (20 for 20%).
    """
    numeric_rate = _to_decimal(rate, field_name)
    if numeric_rate < 0:
        raise ValueError(f"VAT rate cannot be negative for '{field_name}'.")
    if numeric_rate > 1:
        numeric_rate = numeric_rate / Decimal("100")
    if numeric_rate > 1:
        raise ValueError(
            f"VAT rate must be <= 100% for '{field_name}', got {rate!r}."
        )
    return numeric_rate


def _round_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    """Taxable transaction used to calculate VAT payable."""

    jurisdiction: str
    transaction_type: str  # "sale" or "purchase"
    net_amount: Decimal
    vat_rate: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.jurisdiction:
            raise ValueError("Transaction jurisdiction cannot be empty.")

        tx_type = self.transaction_type.lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                "transaction_type must be either 'sale' or 'purchase', "
                f"got {self.transaction_type!r}."
            )
        object.__setattr__(self, "transaction_type", tx_type)

        object.__setattr__(self, "net_amount", _to_decimal(self.net_amount, "net_amount"))
        if self.net_amount < 0:
            raise ValueError("net_amount cannot be negative.")

        if self.vat_rate is not None:
            object.__setattr__(self, "vat_rate", _normalize_rate(self.vat_rate))


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
    default_rates: dict[str, Decimal | int | float | str] | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Calculate output/input VAT and net VAT payable per jurisdiction.

    VAT payable is computed as:
        payable = output_vat_from_sales - input_vat_from_purchases

    Returns a dictionary:
        {
            "DE": {
                "output_vat": Decimal("190.00"),
                "input_vat": Decimal("38.00"),
                "vat_payable": Decimal("152.00"),
            },
            ...
        }
    """
    normalized_default_rates: dict[str, Decimal] = {}
    if default_rates:
        normalized_default_rates = {
            jurisdiction: _normalize_rate(rate, f"default_rate[{jurisdiction}]")
            for jurisdiction, rate in default_rates.items()
        }

    grouped: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for tx in transactions:
        rate = tx.vat_rate
        if rate is None:
            if tx.jurisdiction not in normalized_default_rates:
                raise ValueError(
                    f"Missing VAT rate for jurisdiction '{tx.jurisdiction}'. "
                    "Provide transaction.vat_rate or default_rates entry."
                )
            rate = normalized_default_rates[tx.jurisdiction]

        vat_amount = _round_money(tx.net_amount * rate)
        bucket = grouped[tx.jurisdiction]
        if tx.transaction_type == "sale":
            bucket["output_vat"] = _round_money(bucket["output_vat"] + vat_amount)
        else:
            bucket["input_vat"] = _round_money(bucket["input_vat"] + vat_amount)

    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(grouped):
        output_vat = grouped[jurisdiction]["output_vat"]
        input_vat = grouped[jurisdiction]["input_vat"]
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _round_money(output_vat - input_vat),
        }
    return result


def _read_transactions_csv(path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_cols = {"jurisdiction", "transaction_type", "net_amount"}
        if not required_cols.issubset(reader.fieldnames or []):
            raise ValueError(
                "CSV must include columns: jurisdiction, transaction_type, net_amount. "
                "Optional: vat_rate"
            )

        for row in reader:
            transactions.append(
                Transaction(
                    jurisdiction=(row.get("jurisdiction") or "").strip(),
                    transaction_type=(row.get("transaction_type") or "").strip(),
                    net_amount=(row.get("net_amount") or "").strip(),
                    vat_rate=(row.get("vat_rate") or "").strip() or None,
                )
            )
    return transactions


def _serialize_report(report: dict[str, dict[str, Decimal]]) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {k: f"{v:.2f}" for k, v in metrics.items()}
        for jurisdiction, metrics in report.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction CSV input."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to CSV with columns: jurisdiction, transaction_type, net_amount, [vat_rate]",
    )
    parser.add_argument(
        "--default-rate",
        action="append",
        default=[],
        help="Fallback VAT rate by jurisdiction in format JURISDICTION=RATE (e.g. DE=19 or FR=0.2).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write JSON report. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    default_rates: dict[str, str] = {}
    for item in args.default_rate:
        if "=" not in item:
            raise ValueError(
                f"Invalid --default-rate value {item!r}. Expected format JURISDICTION=RATE."
            )
        jurisdiction, rate = item.split("=", 1)
        default_rates[jurisdiction.strip()] = rate.strip()

    transactions = _read_transactions_csv(Path(args.input))
    report = calculate_vat_payable_by_jurisdiction(transactions, default_rates)
    output_payload = json.dumps(_serialize_report(report), indent=2)

    if args.output:
        Path(args.output).write_text(output_payload + "\n", encoding="utf-8")
    else:
        print(output_payload)


if __name__ == "__main__":
    main()
