from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable, List

from tax.vat import Transaction, compute_vat_payable_by_jurisdiction


def parse_transactions_from_csv(input_csv: Path) -> List[Transaction]:
    transactions: List[Transaction] = []
    with input_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"jurisdiction", "transaction_type", "net_amount", "vat_rate"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            missing = required.difference(set(reader.fieldnames or []))
            raise ValueError(
                "Input CSV missing required columns: " + ", ".join(sorted(missing))
            )

        for idx, row in enumerate(reader, start=2):
            try:
                transactions.append(
                    Transaction(
                        jurisdiction=(row.get("jurisdiction") or "").strip(),
                        transaction_type=(row.get("transaction_type") or "").strip(),
                        net_amount=Decimal((row.get("net_amount") or "0").strip()),
                        vat_rate=Decimal((row.get("vat_rate") or "0").strip()),
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive parsing wrapper
                raise ValueError(f"Invalid data at CSV row {idx}: {row}") from exc

    return transactions


def write_summaries_to_csv(
    output_csv: Path, summaries: Iterable
) -> None:
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["jurisdiction", "output_vat", "input_vat", "vat_payable"]
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "jurisdiction": summary.jurisdiction,
                    "output_vat": f"{summary.output_vat:.2f}",
                    "input_vat": f"{summary.input_vat:.2f}",
                    "vat_payable": f"{summary.vat_payable:.2f}",
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction from transactions CSV."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--output", required=True, help="Path to output CSV file")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_csv = Path(args.input)
    output_csv = Path(args.output)

    transactions = parse_transactions_from_csv(input_csv)
    summaries = compute_vat_payable_by_jurisdiction(transactions)
    write_summaries_to_csv(output_csv, summaries)


if __name__ == "__main__":
    main()
