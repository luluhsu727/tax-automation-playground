"""Tests for vat_check.py CLI script."""
import csv
import tempfile
from pathlib import Path

from vat_check import process_transactions


def _make_csv(rows: list[dict[str, str]], path: Path) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_basic_reconciliation(tmp_path: Path) -> None:
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    summary_csv = tmp_path / "summary.csv"

    _make_csv(
        [
            {"transaction_id": "T1", "country": "DE", "revenue": "100", "vat_collected": "19"},
            {"transaction_id": "T2", "country": "FR", "revenue": "200", "vat_collected": "40"},
        ],
        input_csv,
    )

    process_transactions(input_csv, output_csv, summary_csv)

    assert output_csv.exists()
    assert summary_csv.exists()

    with summary_csv.open() as f:
        reader = list(csv.DictReader(f))
    countries = {r["country"] for r in reader}
    assert countries == {"DE", "FR"}


def test_unknown_country_flagged(tmp_path: Path) -> None:
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    summary_csv = tmp_path / "summary.csv"

    _make_csv(
        [{"transaction_id": "T1", "country": "XX", "revenue": "100", "vat_collected": "10"}],
        input_csv,
    )

    process_transactions(input_csv, output_csv, summary_csv)

    with output_csv.open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["error_flag"] == "True"
    assert rows[0]["error_reason"] == "unknown_country"
