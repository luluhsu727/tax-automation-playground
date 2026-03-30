"""Generate VAT payable totals by jurisdiction from a CSV file."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path

from tax_engine.vat import Transaction, calculate_vat_payable_by_jurisdiction


def load_transactions(csv_path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_columns = {"jurisdiction", "transaction_type", "net_amount"}
        if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
            raise ValueError(
                "Input CSV must include columns: "
                "jurisdiction, transaction_type, net_amount "
                "(optional: vat_rate, vat_amount)."
            )

        for row in reader:
            if not row["jurisdiction"] or not row["transaction_type"] or not row["net_amount"]:
                raise ValueError(f"Missing required values in row: {row}")

            vat_rate = Decimal(row["vat_rate"]) if row.get("vat_rate") else None
            vat_amount = Decimal(row["vat_amount"]) if row.get("vat_amount") else None

            transactions.append(
                Transaction(
                    jurisdiction=row["jurisdiction"],
                    transaction_type=row["transaction_type"],
                    net_amount=Decimal(row["net_amount"]),
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                )
            )

    return transactions


def write_report(report_path: Path, totals: dict[str, Decimal]) -> None:
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["jurisdiction", "vat_payable"])
        writer.writeheader()
        for jurisdiction, vat_payable in totals.items():
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "vat_payable": f"{vat_payable:.2f}",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to source transactions CSV.",
    )
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Path for generated VAT payable report CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    transactions = load_transactions(input_path)
    totals = calculate_vat_payable_by_jurisdiction(transactions)
    write_report(output_path, totals)

    print(f"Wrote VAT payable report for {len(totals)} jurisdictions to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
