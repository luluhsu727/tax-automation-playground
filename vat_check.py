#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path


VAT_RATES = {
    "DE": 0.19,
    "FR": 0.20,
    "ES": 0.21,
}


def print_summary_table(summary_rows: list[dict[str, str]]) -> None:
    headers = [
        "country",
        "total_revenue",
        "total_vat_collected",
        "total_expected_vat",
        "variance",
    ]
    widths = {
        header: max(len(header), *(len(row[header]) for row in summary_rows))
        for header in headers
    }

    separator = "-+-".join("-" * widths[header] for header in headers)
    header_row = " | ".join(header.ljust(widths[header]) for header in headers)
    print("\nReconciliation summary by country")
    print(header_row)
    print(separator)
    for row in summary_rows:
        print(" | ".join(row[header].rjust(widths[header]) for header in headers))


def process_transactions(
    input_path: Path, output_path: Path, summary_output_path: Path
) -> None:
    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])

        required = {"transaction_id", "country", "revenue", "vat_collected"}
        missing = required - set(fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        output_fields = fieldnames + [
            "vat_rate",
            "expected_vat",
            "vat_difference",
            "variance",
            "error_flag",
            "error_reason",
        ]

        processed_rows = []
        summary_totals: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "total_revenue": 0.0,
                "total_vat_collected": 0.0,
                "total_expected_vat": 0.0,
            }
        )

        for row in reader:
            country = (row.get("country") or "").strip().upper()
            vat_rate = VAT_RATES.get(country, 0.0)

            revenue = float(row["revenue"])
            vat_collected = float(row["vat_collected"])
            expected_vat = revenue * vat_rate
            vat_difference = expected_vat - vat_collected
            variance = abs(vat_difference)

            unknown_country = country not in VAT_RATES
            diff_exceeds_threshold = variance > 1
            error_flag = unknown_country or diff_exceeds_threshold

            if unknown_country:
                error_reason = "unknown_country"
            elif diff_exceeds_threshold:
                error_reason = "vat_mismatch"
            else:
                error_reason = ""

            row.update(
                {
                    "revenue": f"{revenue:.2f}",
                    "vat_collected": f"{vat_collected:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "expected_vat": f"{expected_vat:.2f}",
                    "vat_difference": f"{vat_difference:.2f}",
                    "variance": f"{variance:.2f}",
                    "error_flag": str(error_flag),
                    "error_reason": error_reason,
                }
            )
            processed_rows.append(row)
            summary_totals[country]["total_revenue"] += revenue
            summary_totals[country]["total_vat_collected"] += vat_collected
            summary_totals[country]["total_expected_vat"] += expected_vat

        processed_rows.sort(key=lambda r: float(r["variance"]), reverse=True)

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fields)
            writer.writeheader()
            for row in processed_rows:
                writer.writerow(row)

    summary_rows = []
    for country in sorted(summary_totals):
        totals = summary_totals[country]
        variance = totals["total_expected_vat"] - totals["total_vat_collected"]
        summary_rows.append(
            {
                "country": country,
                "total_revenue": f"{totals['total_revenue']:.2f}",
                "total_vat_collected": f"{totals['total_vat_collected']:.2f}",
                "total_expected_vat": f"{totals['total_expected_vat']:.2f}",
                "variance": f"{variance:.2f}",
            }
        )

    summary_fields = [
        "country",
        "total_revenue",
        "total_vat_collected",
        "total_expected_vat",
        "variance",
    ]
    with summary_output_path.open("w", newline="", encoding="utf-8") as summary_file:
        writer = csv.DictWriter(summary_file, fieldnames=summary_fields)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    print_summary_table(summary_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate expected VAT and flag transaction errors."
    )
    parser.add_argument(
        "--input",
        default="/home/ubuntu/.cursor/projects/workspace/uploads/practice_dataset_-_Sheet1.csv",
        help="Path to source transactions CSV",
    )
    parser.add_argument(
        "--output",
        default="vat_check_results.csv",
        help="Path to output CSV with VAT checks",
    )
    parser.add_argument(
        "--summary-output",
        default="vat_reconciliation_summary.csv",
        help="Path to output CSV with reconciliation summary by country",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_output_path = Path(args.summary_output)
    process_transactions(input_path, output_path, summary_output_path)
    print(f"Wrote VAT validation results to: {output_path}")
    print(f"Wrote reconciliation summary to: {summary_output_path}")


if __name__ == "__main__":
    main()
