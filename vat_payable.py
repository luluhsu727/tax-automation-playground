"""Generate VAT payable amounts per jurisdiction.

Core rule:
    VAT payable = output VAT (sales) - input VAT (purchases)
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

_TWO_DP = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a value to Decimal with a clear validation error."""
    if value is None or value == "":
        raise ValueError(f"Missing required value for '{field_name}'.")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _normalize_rate(raw_rate: Any) -> Decimal:
    """Normalize VAT rate to decimal form.

    Supports:
    - 0.20 for 20%
    - 20 for 20%
    """
    rate = _to_decimal(raw_rate, "vat_rate")
    if rate < 0:
        raise ValueError("VAT rate cannot be negative.")
    if rate > 1:
        if rate > 100:
            raise ValueError("VAT rate above 100% is invalid.")
        return (rate / Decimal("100")).quantize(Decimal("0.0001"))
    return rate


def _normalize_transaction_type(raw_type: Any) -> str:
    transaction_type = str(raw_type).strip().lower()
    if transaction_type not in {"sale", "purchase"}:
        raise ValueError(
            f"Unsupported transaction_type {raw_type!r}. Use 'sale' or 'purchase'."
        )
    return transaction_type


def _compute_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Compute VAT amount for a single transaction.

    Precedence:
      1) explicit `vat_amount` when provided
      2) `net_amount * vat_rate`
    """
    if transaction.get("vat_amount") not in (None, ""):
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        if vat_amount < 0:
            raise ValueError("VAT amount cannot be negative.")
        return vat_amount.quantize(_TWO_DP, rounding=ROUND_HALF_UP)

    net_amount = _to_decimal(transaction.get("net_amount"), "net_amount")
    if net_amount < 0:
        raise ValueError("Net amount cannot be negative.")
    vat_rate = _normalize_rate(transaction.get("vat_rate"))
    return (net_amount * vat_rate).quantize(_TWO_DP, rounding=ROUND_HALF_UP)


def generate_vat_summary_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Generate output VAT, input VAT, and VAT payable per jurisdiction."""
    buckets: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty 'jurisdiction'.")

        transaction_type = _normalize_transaction_type(transaction.get("transaction_type"))
        vat_amount = _compute_transaction_vat(transaction)

        if transaction_type == "sale":
            buckets[jurisdiction]["output_vat"] += vat_amount
        else:
            buckets[jurisdiction]["input_vat"] += vat_amount

    summary: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(buckets):
        output_vat = buckets[jurisdiction]["output_vat"].quantize(
            _TWO_DP, rounding=ROUND_HALF_UP
        )
        input_vat = buckets[jurisdiction]["input_vat"].quantize(
            _TWO_DP, rounding=ROUND_HALF_UP
        )
        summary[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": (output_vat - input_vat).quantize(
                _TWO_DP, rounding=ROUND_HALF_UP
            ),
        }
    return summary


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Return only VAT payable totals per jurisdiction."""
    summary = generate_vat_summary_by_jurisdiction(transactions)
    return {jurisdiction: values["vat_payable"] for jurisdiction, values in summary.items()}


def read_transactions_from_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read transaction rows from CSV."""
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_summary_to_csv(
    summary: Mapping[str, Mapping[str, Decimal]], output_path: str | Path
) -> None:
    """Write jurisdiction summary to CSV."""
    path = Path(output_path)
    fieldnames = ["jurisdiction", "output_vat", "input_vat", "vat_payable"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for jurisdiction in sorted(summary):
            row = summary[jurisdiction]
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "output_vat": f"{row['output_vat']:.2f}",
                    "input_vat": f"{row['input_vat']:.2f}",
                    "vat_payable": f"{row['vat_payable']:.2f}",
                }
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount per jurisdiction from transactions CSV."
    )
    parser.add_argument("input_csv", help="Path to input transactions CSV")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_csv",
        default="vat_payable_by_jurisdiction.csv",
        help="Path to output VAT summary CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    transactions = read_transactions_from_csv(args.input_csv)
    summary = generate_vat_summary_by_jurisdiction(transactions)
    write_summary_to_csv(summary, args.output_csv)


if __name__ == "__main__":
    main()
