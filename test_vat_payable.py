"""Tests for VAT payable generation per jurisdiction."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from vat_payable import generate_vat_payable_by_jurisdiction


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as input_file:
        return list(csv.DictReader(input_file))


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_csv = temp_path / "transactions.csv"
            output_csv = temp_path / "vat_payable_by_jurisdiction.csv"

            _write_csv(
                input_csv,
                [
                    {
                        "transaction_id": "TX-1",
                        "jurisdiction": "de",
                        "revenue": "100.00",
                        "vat_collected": "10.00",
                    },
                    {
                        "transaction_id": "TX-2",
                        "jurisdiction": "DE",
                        "revenue": "50.00",
                        "vat_collected": "12.00",
                    },
                    {
                        "transaction_id": "TX-3",
                        "jurisdiction": "FR",
                        "revenue": "200.00",
                        "vat_collected": "30.00",
                    },
                ],
            )

            generate_vat_payable_by_jurisdiction(input_csv, output_csv)

            self.assertEqual(
                _read_csv(output_csv),
                [
                    {
                        "jurisdiction": "DE",
                        "total_revenue": "150.00",
                        "total_vat_collected": "22.00",
                        "total_expected_vat": "28.50",
                        "vat_to_be_paid": "6.50",
                    },
                    {
                        "jurisdiction": "FR",
                        "total_revenue": "200.00",
                        "total_vat_collected": "30.00",
                        "total_expected_vat": "40.00",
                        "vat_to_be_paid": "10.00",
                    },
                ],
            )

    def test_supports_country_column_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_csv = temp_path / "transactions_country.csv"
            output_csv = temp_path / "vat_payable_by_jurisdiction.csv"

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

            generate_vat_payable_by_jurisdiction(input_csv, output_csv)

            self.assertEqual(
                _read_csv(output_csv),
                [
                    {
                        "jurisdiction": "ES",
                        "total_revenue": "100.00",
                        "total_vat_collected": "0.00",
                        "total_expected_vat": "21.00",
                        "vat_to_be_paid": "21.00",
                    }
                ],
            )

    def test_rejects_unsupported_jurisdiction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_csv = temp_path / "transactions_unknown.csv"
            output_csv = temp_path / "vat_payable_by_jurisdiction.csv"

            _write_csv(
                input_csv,
                [
                    {
                        "transaction_id": "TX-1",
                        "jurisdiction": "XX",
                        "revenue": "100.00",
                        "vat_collected": "20.00",
                    }
                ],
            )

            with self.assertRaises(ValueError) as exc_info:
                generate_vat_payable_by_jurisdiction(input_csv, output_csv)

            self.assertIn("Unsupported jurisdiction code: XX", str(exc_info.exception))


if __name__ == "__main__":
    unittest.main()
