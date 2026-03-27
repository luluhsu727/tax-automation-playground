from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tax.vat import JurisdictionVatSummary, Transaction


def parse_transactions_from_csv(path: Path) -> list[Transaction]:
    with path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        required = {"jurisdiction", "transaction_type", "net_amount", "vat_rate"}
        missing = required - set(fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        return [
            Transaction(
                row["jurisdiction"],
                row["transaction_type"],
                row["net_amount"],
                row["vat_rate"],
            )
            for row in reader
        ]


def write_summaries_to_csv(path: Path, summaries: list[JurisdictionVatSummary]) -> None:
    fields = ["jurisdiction", "output_vat", "input_vat", "vat_payable"]
    with path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fields)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable summary for each jurisdiction from CSV input."
    )
    parser.add_argument("--input", required=True, help="Input CSV with transactions")
    parser.add_argument("--output", required=True, help="Output CSV for jurisdiction summary")
    return parser.parse_args()


def main() -> None:
    from tax.vat import compute_vat_payable_by_jurisdiction

    args = parse_args()
    transactions = parse_transactions_from_csv(Path(args.input))
    summaries = compute_vat_payable_by_jurisdiction(transactions)
    write_summaries_to_csv(Path(args.output), summaries)
    print(f"Wrote VAT summary to: {args.output}")


if __name__ == "__main__":
    main()
