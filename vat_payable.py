"""Generate VAT payable amounts per jurisdiction.

The core rule applied here is:
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
    """Convert a value into Decimal with a clear error on failure."""
    if value is None or value == "":
        raise ValueError(f"Missing required value for '{field_name}'.")
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _normalize_rate(raw_rate: Any) -> Decimal:
    """Normalize VAT rate.

    Accepts either decimal form (0.2 for 20%) or whole-percent form (20 for 20%).
    """
    rate = _to_decimal(raw_rate, "vat_rate")
    if rate < 0:
        raise ValueError("VAT rate cannot be negative.")
    if rate > 1:
        if rate > 100:
            raise ValueError("VAT rate above 100% is invalid.")
        return (rate / Decimal("100")).quantize(Decimal("0.0001"))
    return rate


def _normalize_type(raw_type: Any) -> str:
    tx_type = str(raw_type).strip().lower()
    if tx_type not in {"sale", "purchase"}:
        raise ValueError(
            f"Unsupported transaction_type {raw_type!r}. Use 'sale' or 'purchase'."
        )
    return tx_type


def _compute_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Compute VAT amount for a single transaction.

    Precedence:
      1) explicit `vat_amount` if provided
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
    rate = _normalize_rate(transaction.get("vat_rate"))
    return (net_amount * rate).quantize(_TWO_DP, rounding=ROUND_HALF_UP)


def generate_vat_summary_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Return VAT summary per jurisdiction.

    Output structure:
    {
        "DE": {"output_vat": Decimal("20.00"), "input_vat": Decimal("5.00"), "vat_payable": Decimal("15.00")},
        ...
    }
    """
    buckets: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction must include a non-empty 'jurisdiction'.")

        tx_type = _normalize_type(transaction.get("transaction_type"))
        vat_amount = _compute_transaction_vat(transaction)

        if tx_type == "sale":
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
    """Return VAT payable per jurisdiction as a thin convenience wrapper."""
    summary = generate_vat_summary_by_jurisdiction(transactions)
    return {k: v["vat_payable"] for k, v in summary.items()}


def read_transactions_from_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Load transactions from CSV file.

    Expected columns:
      - jurisdiction
      - transaction_type ('sale' or 'purchase')
      - either vat_amount OR net_amount + vat_rate
    """
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_summary_to_csv(
    summary: Mapping[str, Mapping[str, Decimal]],
    output_path: str | Path,
) -> None:
    """Write jurisdiction VAT summary to CSV."""
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
        description="Generate VAT payable amount per jurisdiction from transaction CSV."
    )
    parser.add_argument("input_csv", help="Path to input transactions CSV")
    parser.add_argument(
        "-o",
        "--output",
        dest="output_csv",
        default="vat_payable_by_jurisdiction.csv",
        help="Path to output summary CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    transactions = read_transactions_from_csv(args.input_csv)
    summary = generate_vat_summary_by_jurisdiction(transactions)
    write_summary_to_csv(summary, args.output_csv)


if __name__ == "__main__":
    main()
