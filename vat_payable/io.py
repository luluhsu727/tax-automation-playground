from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable

from .calculator import Transaction, calculate_vat_payable_by_jurisdiction


def load_transactions_from_csv(path: str | Path) -> list[Transaction]:
    transactions: list[Transaction] = []

    with open(path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"jurisdiction", "amount", "vat_rate", "transaction_type"}

        if reader.fieldnames is None:
            raise ValueError("CSV file must include a header row.")

        missing = required_columns.difference(set(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV file missing required columns: {sorted(missing)}")

        for row in reader:
            vat_amount = row.get("vat_amount")
            transactions.append(
                Transaction(
                    jurisdiction=row["jurisdiction"],
                    amount=row["amount"],
                    vat_rate=row["vat_rate"],
                    transaction_type=row["transaction_type"],
                    vat_amount=vat_amount if vat_amount not in (None, "") else None,
                )
            )

    return transactions


def write_report_csv(path: str | Path, rows: Iterable[dict]) -> None:
    rows_list = list(rows)
    fieldnames = ["jurisdiction", "output_vat", "input_vat", "vat_to_be_paid"]

    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_list:
            writer.writerow(row)


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction from a transactions CSV."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV with transactions.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json", "csv"),
        default="table",
        help="Output format. Defaults to table.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path (required for --format csv).",
    )
    args = parser.parse_args(argv)

    transactions = load_transactions_from_csv(args.input)
    result = calculate_vat_payable_by_jurisdiction(transactions)
    rows = [{"jurisdiction": k, **v} for k, v in sorted(result.items())]

    if args.format == "csv":
        if not args.output:
            parser.error("--output is required when --format csv is used.")
        write_report_csv(args.output, rows)
        return 0

    if args.format == "json":
        payload = json.dumps(rows, indent=2, sort_keys=True)
    else:
        header = "jurisdiction,output_vat,input_vat,vat_to_be_paid"
        lines = [header]
        for row in rows:
            lines.append(
                f'{row["jurisdiction"]},{row["output_vat"]:.2f},{row["input_vat"]:.2f},{row["vat_to_be_paid"]:.2f}'
            )
        payload = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0
