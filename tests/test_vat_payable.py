import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import calculate_vat_payable, generate_vat_payable


class TestVatPayable(unittest.TestCase):
    def test_calculates_vat_payable_grouped_by_jurisdiction(self) -> None:
        records = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": "19.00",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "vat_amount": "4.20",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sales",
                "net_amount": "100.00",
                "vat_rate": "0.20",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "input",
                "net_amount": "50.00",
                "vat_rate": "0.20",
            },
        ]

        summaries = calculate_vat_payable(records)
        by_jurisdiction = {summary.jurisdiction: summary for summary in summaries}

        self.assertEqual(by_jurisdiction["DE"].output_vat, Decimal("19.00"))
        self.assertEqual(by_jurisdiction["DE"].input_vat, Decimal("4.20"))
        self.assertEqual(by_jurisdiction["DE"].vat_payable, Decimal("14.80"))

        self.assertEqual(by_jurisdiction["FR"].output_vat, Decimal("20.00"))
        self.assertEqual(by_jurisdiction["FR"].input_vat, Decimal("10.00"))
        self.assertEqual(by_jurisdiction["FR"].vat_payable, Decimal("10.00"))

    def test_generates_output_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "transactions.csv"
            output_path = Path(tmp_dir) / "vat_summary.csv"

            with input_path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=[
                        "jurisdiction",
                        "transaction_type",
                        "net_amount",
                        "vat_rate",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "jurisdiction": "ES",
                        "transaction_type": "sale",
                        "net_amount": "250.00",
                        "vat_rate": "0.21",
                    }
                )
                writer.writerow(
                    {
                        "jurisdiction": "ES",
                        "transaction_type": "purchase",
                        "net_amount": "100.00",
                        "vat_rate": "0.21",
                    }
                )

            summaries = generate_vat_payable(input_path, output_path)

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].vat_payable, Decimal("31.50"))

            with output_path.open("r", encoding="utf-8", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                rows = list(reader)

            self.assertEqual(
                rows,
                [
                    {
                        "jurisdiction": "ES",
                        "output_vat": "52.50",
                        "input_vat": "21.00",
                        "vat_payable": "31.50",
                    }
                ],
            )

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing jurisdiction"):
            calculate_vat_payable(
                [{"transaction_type": "sale", "vat_amount": "10.00"}]
            )


if __name__ == "__main__":
    unittest.main()
