"""Utilities to generate VAT payable amounts per jurisdiction.

This module supports two entry points:
1) Library usage via ``calculate_vat_by_jurisdiction``.
2) CLI usage for CSV inputs:
   python vat_payable.py transactions.csv --rate DE=0.19 --rate FR=0.20
"""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


TWOPLACES = Decimal("0.01")


def _as_decimal(value: Any, field_name: str) -> Decimal:
    """Convert incoming value into Decimal with explicit error context."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value}") from exc


def _round_currency(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_vat_by_jurisdiction(
    transactions: list[dict[str, Any]],
    default_vat_rates: dict[str, float | Decimal] | None = None,
) -> dict[str, dict[str, float]]:
    """Return VAT output/input/payable grouped by jurisdiction.

    Args:
        transactions: list of transaction dicts. Supported keys:
            - jurisdiction (required)
            - kind (required): "sale" or "purchase"
            - amount (required unless vat_amount is provided)
            - vat_rate (optional if default_vat_rates provides the jurisdiction)
            - vat_amount (optional explicit VAT amount for the transaction)
        default_vat_rates: fallback VAT rates by jurisdiction.

    Returns:
        Mapping:
            {
                "DE": {
                    "output_vat": 190.0,
                    "input_vat": 19.0,
                    "vat_payable": 171.0
                }
            }
    """
    rates: dict[str, Decimal] = {
        jurisdiction: _as_decimal(rate, f"default_vat_rates[{jurisdiction}]")
        for jurisdiction, rate in (default_vat_rates or {}).items()
    }
    totals: dict[str, dict[str, Decimal]] = {}

    for idx, tx in enumerate(transactions):
        jurisdiction = str(tx.get("jurisdiction", "")).strip()
        kind = str(tx.get("kind", "")).strip().lower()
        if not jurisdiction:
            raise ValueError(f"Transaction #{idx} is missing 'jurisdiction'")
        if kind not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction #{idx} has invalid 'kind': {tx.get('kind')!r}. "
                "Expected 'sale' or 'purchase'."
            )

        if "vat_amount" in tx and tx["vat_amount"] not in (None, ""):
            vat_amount = _as_decimal(tx["vat_amount"], "vat_amount")
        else:
            amount = _as_decimal(tx.get("amount"), "amount")
            if "vat_rate" in tx and tx["vat_rate"] not in (None, ""):
                rate = _as_decimal(tx["vat_rate"], "vat_rate")
            elif jurisdiction in rates:
                rate = rates[jurisdiction]
            else:
                raise ValueError(
                    f"Transaction #{idx} has no VAT rate for jurisdiction "
                    f"'{jurisdiction}'. Provide tx.vat_rate or default_vat_rates."
                )
            vat_amount = amount * rate

        jurisdiction_totals = totals.setdefault(
            jurisdiction,
            {
                "output_vat": Decimal("0"),
                "input_vat": Decimal("0"),
            },
        )
        if kind == "sale":
            jurisdiction_totals["output_vat"] += vat_amount
        else:
            jurisdiction_totals["input_vat"] += vat_amount

    result: dict[str, dict[str, float]] = {}
    for jurisdiction, bucket in sorted(totals.items()):
        output_vat = _round_currency(bucket["output_vat"])
        input_vat = _round_currency(bucket["input_vat"])
        vat_payable = _round_currency(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }
    return result


def load_transactions_from_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Load transaction rows from CSV into a list of dictionaries."""
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_rate_flags(rate_flags: list[str]) -> dict[str, Decimal]:
    """Parse CLI --rate values in form JURISDICTION=RATE."""
    parsed: dict[str, Decimal] = {}
    for flag in rate_flags:
        if "=" not in flag:
            raise ValueError(
                f"Invalid --rate value '{flag}'. Expected format JURISDICTION=RATE."
            )
        jurisdiction, rate_str = flag.split("=", 1)
        jurisdiction = jurisdiction.strip()
        if not jurisdiction:
            raise ValueError(f"Invalid --rate value '{flag}': empty jurisdiction.")
        parsed[jurisdiction] = _as_decimal(rate_str, f"rate[{jurisdiction}]")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable per jurisdiction from a CSV file."
    )
    parser.add_argument(
        "csv_file",
        help="Path to CSV with columns jurisdiction,kind,amount[,vat_rate|vat_amount]",
    )
    parser.add_argument(
        "--rate",
        action="append",
        default=[],
        help="Fallback default VAT rate as JURISDICTION=RATE (repeatable).",
    )
    args = parser.parse_args()

    default_rates = parse_rate_flags(args.rate)
    transactions = load_transactions_from_csv(args.csv_file)
    result = calculate_vat_by_jurisdiction(transactions, default_rates)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
