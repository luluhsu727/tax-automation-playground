"""Command-line interface for VAT payable by jurisdiction."""

from __future__ import annotations

import argparse
from pathlib import Path

from .vat import load_transactions_from_csv, summarize_vat_by_jurisdiction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vat-payable",
        description="Generate VAT to be paid for each jurisdiction from a CSV file.",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to transactions CSV file.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    transactions = load_transactions_from_csv(args.csv_path)
    summary = summarize_vat_by_jurisdiction(transactions)

    print("jurisdiction,output_vat,input_vat,vat_payable,transaction_count")
    for row in summary.values():
        print(
            f"{row.jurisdiction},{row.output_vat},{row.input_vat},"
            f"{row.vat_payable},{row.transaction_count}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
