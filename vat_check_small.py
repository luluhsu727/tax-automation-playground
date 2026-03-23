from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


VAT_RATES = {
    "DE": 0.19,
    "FR": 0.20,
    "ES": 0.21,
    "IT": 0.22,
}


def resolve_input_path(input_path: Path) -> Path:
    if input_path.exists():
        return input_path

    if input_path.name == "eu_transactions.csv":
        fallback_paths = [
            Path("eu_transactions_-_Sheet1.csv"),
            Path("/home/ubuntu/.cursor/projects/workspace/uploads/eu_transactions_-_Sheet1.csv"),
        ]
        for fallback in fallback_paths:
            if fallback.exists():
                return fallback

    raise FileNotFoundError(f"Could not find input CSV at: {input_path}")


def build_vat_tables(input_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(input_csv)

    required_cols = {"transaction_id", "country", "revenue", "vat_collected"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

    df["vat_rate"] = df["country"].map(VAT_RATES)
    unknown_country_mask = df["vat_rate"].isna()
    if unknown_country_mask.any():
        unknown_countries = sorted(df.loc[unknown_country_mask, "country"].dropna().unique())
        raise ValueError(f"Unsupported country codes found: {unknown_countries}")

    df["expected_vat"] = df["revenue"] * df["vat_rate"]
    df["variance"] = df["expected_vat"] - df["vat_collected"]
    df["flag_anomaly"] = df["variance"] > 1

    summary = (
        df.groupby("country", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_vat_collected=("vat_collected", "sum"),
            total_expected_vat=("expected_vat", "sum"),
            total_variance=("variance", "sum"),
        )
        .sort_values("country")
    )

    return df, summary


def main() -> None:
    print("Current working directory:", os.getcwd())

    parser = argparse.ArgumentParser(description="VAT reconciliation for EU transactions.")
    parser.add_argument(
        "--input",
        default="eu_transactions.csv",
        help="Path to input CSV file (default: eu_transactions.csv).",
    )
    parser.add_argument(
        "--output",
        default="vat_report.xlsx",
        help="Path to output Excel file (default: vat_report.xlsx).",
    )
    args = parser.parse_args()

    input_path = resolve_input_path(Path(args.input))
    transactions_df, summary_df = build_vat_tables(input_path)

    with pd.ExcelWriter(args.output, engine="openpyxl") as writer:
        transactions_df.to_excel(writer, index=False, sheet_name="Sheet1")
        summary_df.to_excel(writer, index=False, sheet_name="Sheet2")

    print("Transaction-level table:")
    print(transactions_df.to_string(index=False))
    print("\nSummary table by country:")
    print(summary_df.to_string(index=False))
    print(f"\nSaved report to: {args.output}")


if __name__ == "__main__":
    main()
