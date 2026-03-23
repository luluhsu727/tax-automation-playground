#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


VAT_RATES = {
    "DE": 0.19,
    "FR": 0.20,
    "ES": 0.21,
}


def process_transactions(input_path: Path, output_path: Path) -> None:
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
            "error_flag",
            "error_reason",
        ]

        with output_path.open("w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fields)
            writer.writeheader()

            for row in reader:
                country = (row.get("country") or "").strip().upper()
                vat_rate = VAT_RATES.get(country, 0.0)

                revenue = float(row["revenue"])
                vat_collected = float(row["vat_collected"])
                expected_vat = revenue * vat_rate
                vat_difference = expected_vat - vat_collected

                unknown_country = country not in VAT_RATES
                diff_exceeds_threshold = abs(vat_difference) > 1
                error_flag = unknown_country or diff_exceeds_threshold

                if unknown_country:
                    error_reason = "unknown_country"
                elif diff_exceeds_threshold:
                    error_reason = "vat_mismatch"
                else:
                    error_reason = ""

                row.update(
                    {
                        "vat_rate": f"{vat_rate:.2f}",
                        "expected_vat": f"{expected_vat:.2f}",
                        "vat_difference": f"{vat_difference:.2f}",
                        "error_flag": str(error_flag),
                        "error_reason": error_reason,
                    }
                )
                writer.writerow(row)


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    process_transactions(input_path, output_path)
    print(f"Wrote VAT validation results to: {output_path}")


if __name__ == "__main__":
    main()
