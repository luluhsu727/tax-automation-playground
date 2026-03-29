"""Generate VAT payable values by jurisdiction.

Input transactions are grouped by jurisdiction and categorized as:
- sale: contributes to output VAT (VAT collected)
- purchase: contributes to input VAT (VAT paid)

VAT payable is computed as:
    output_vat - input_vat
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Iterable, List


TWOPLACES = Decimal("0.01")


def _to_decimal(value: str) -> Decimal:
    """Safely parse decimal values from text."""
    return Decimal(value.strip())


def _money(value: Decimal) -> Decimal:
    """Round to currency precision."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal

    def vat_amount(self) -> Decimal:
        return _money(self.net_amount * self.vat_rate)


def read_transactions_from_csv(path: str | Path) -> List[Transaction]:
    """Read transactions from CSV.

    Required columns:
    - jurisdiction
    - transaction_type (sale|purchase)
    - net_amount
    - vat_rate (e.g. 0.20 for 20%)
    """
    transactions: List[Transaction] = []

    with Path(path).open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        required = {"jurisdiction", "transaction_type", "net_amount", "vat_rate"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

        for row_number, row in enumerate(reader, start=2):
            jurisdiction = (row.get("jurisdiction") or "").strip()
            tx_type = (row.get("transaction_type") or "").strip().lower()
            if tx_type not in {"sale", "purchase"}:
                raise ValueError(
                    f"Invalid transaction_type at row {row_number}: {tx_type!r}"
                )
            if not jurisdiction:
                raise ValueError(f"Empty jurisdiction at row {row_number}")

            try:
                net_amount = _to_decimal(row["net_amount"])
                vat_rate = _to_decimal(row["vat_rate"])
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    f"Invalid numeric value at row {row_number}: {row}"
                ) from exc

            transactions.append(
                Transaction(
                    jurisdiction=jurisdiction,
                    transaction_type=tx_type,
                    net_amount=net_amount,
                    vat_rate=vat_rate,
                )
            )

    return transactions


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> Dict[str, Dict[str, Decimal]]:
    """Return VAT output/input/payable per jurisdiction."""
    totals: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
            "vat_to_be_paid": Decimal("0"),
        }
    )

    for tx in transactions:
        vat = tx.vat_amount()
        if tx.transaction_type == "sale":
            totals[tx.jurisdiction]["output_vat"] += vat
        else:  # purchase
            totals[tx.jurisdiction]["input_vat"] += vat

    for jurisdiction, values in totals.items():
        output_vat = _money(values["output_vat"])
        input_vat = _money(values["input_vat"])
        payable = _money(output_vat - input_vat)
        totals[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_to_be_paid": payable,
        }

    return dict(totals)


def _as_serializable(result: Dict[str, Dict[str, Decimal]]) -> Dict[str, Dict[str, str]]:
    return {
        jurisdiction: {key: f"{value:.2f}" for key, value in values.items()}
        for jurisdiction, values in sorted(result.items())
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction from a CSV file."
    )
    parser.add_argument("input_csv", help="Path to input CSV")
    parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="json",
        help="Output format (default: json)",
    )
    return parser


def _render_table(result: Dict[str, Dict[str, str]]) -> str:
    headers = ["jurisdiction", "output_vat", "input_vat", "vat_to_be_paid"]
    rows = [[j, v["output_vat"], v["input_vat"], v["vat_to_be_paid"]] for j, v in result.items()]
    widths = [
        max(len(headers[idx]), *(len(row[idx]) for row in rows)) if rows else len(headers[idx])
        for idx in range(len(headers))
    ]
    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * widths[i] for i in range(len(headers)))
    body = [" | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) for row in rows]
    return "\n".join([line, sep, *body])


def main() -> int:
    parser = _build_cli()
    args = parser.parse_args()

    transactions = read_transactions_from_csv(args.input_csv)
    result = calculate_vat_payable_by_jurisdiction(transactions)
    serializable = _as_serializable(result)

    if args.format == "json":
        print(json.dumps(serializable, indent=2, sort_keys=True))
    else:
        print(_render_table(serializable))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
