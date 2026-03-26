"""Tests for CSV VAT payable generation by jurisdiction."""

from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from vat_check import process_transactions


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_vat_payable_summary_for_jurisdictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            input_csv = base / "input.csv"
            output_csv = base / "transactions.csv"
            summary_csv = base / "summary.csv"

            _write_csv(
                input_csv,
                [
                    {
                        "transaction_id": "TX-1",
                        "jurisdiction": "de",
                        "revenue": "100.00",
                        "vat_collected": "15.00",
                    },
                    {
                        "transaction_id": "TX-2",
                        "jurisdiction": "DE",
                        "revenue": "50.00",
                        "vat_collected": "10.00",
                    },
                    {
                        "transaction_id": "TX-3",
                        "jurisdiction": "FR",
                        "revenue": "200.00",
                        "vat_collected": "30.00",
                    },
                ],
            )

            process_transactions(input_csv, output_csv, summary_csv)

            summary_rows = _read_csv(summary_csv)
            self.assertEqual(
                summary_rows,
                [
                    {
                        "jurisdiction": "DE",
                        "total_revenue": "150.00",
                        "total_vat_collected": "25.00",
                        "total_expected_vat": "28.50",
                        "vat_payable": "3.50",
                    },
                    {
                        "jurisdiction": "FR",
                        "total_revenue": "200.00",
                        "total_vat_collected": "30.00",
                        "total_expected_vat": "40.00",
                        "vat_payable": "10.00",
                    },
                ],
            )

            transaction_rows = _read_csv(output_csv)
            self.assertEqual(transaction_rows[0]["transaction_id"], "TX-3")
            self.assertEqual(transaction_rows[0]["vat_payable"], "10.00")
            self.assertEqual(transaction_rows[-1]["transaction_id"], "TX-2")

    def test_supports_country_alias_and_rejects_unknown_jurisdiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            input_csv = base / "input_country.csv"
            output_csv = base / "transactions_country.csv"
            summary_csv = base / "summary_country.csv"

            _write_csv(
                input_csv,
                [
                    {
                        "transaction_id": "TX-1",
                        "country": "ES",
                        "revenue": "100.00",
                        "vat_collected": "0.00",
                    }
                ],
            )

            process_transactions(input_csv, output_csv, summary_csv)
            summary_rows = _read_csv(summary_csv)
            self.assertEqual(summary_rows[0]["jurisdiction"], "ES")
            self.assertEqual(summary_rows[0]["vat_payable"], "21.00")

            _write_csv(
                input_csv,
                [
                    {
                        "transaction_id": "TX-2",
                        "country": "XX",
                        "revenue": "100.00",
                        "vat_collected": "0.00",
                    }
                ],
            )

            with self.assertRaisesRegex(
                ValueError, "Unsupported jurisdiction code: XX"
            ):
                process_transactions(input_csv, output_csv, summary_csv)


if __name__ == "__main__":
    unittest.main()
