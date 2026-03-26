import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    generate_vat_payable_by_jurisdiction,
    generate_vat_summary_by_jurisdiction,
    read_transactions_from_csv,
    write_summary_to_csv,
)


class VatPayableTests(unittest.TestCase):
    def test_generate_summary_for_multiple_jurisdictions(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "net_amount": "100.00",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "net_amount": "50.00",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": "20.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "25.00",
            },
        ]

        summary = generate_vat_summary_by_jurisdiction(transactions)

        self.assertEqual(
            summary["DE"],
            {
                "output_vat": Decimal("19.00"),
                "input_vat": Decimal("9.50"),
                "vat_payable": Decimal("9.50"),
            },
        )
        self.assertEqual(
            summary["FR"],
            {
                "output_vat": Decimal("20.00"),
                "input_vat": Decimal("25.00"),
                "vat_payable": Decimal("-5.00"),
            },
        )

    def test_generate_vat_payable_wrapper(self) -> None:
        transactions = [
            {
                "jurisdiction": "GB",
                "transaction_type": "sale",
                "net_amount": "100",
                "vat_rate": "20",  # whole-percent form
            },
            {
                "jurisdiction": "GB",
                "transaction_type": "purchase",
                "net_amount": "40",
                "vat_rate": "20",
            },
        ]
        payable = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(payable, {"GB": Decimal("12.00")})

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_summary_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "transaction_type": "refund",
                        "vat_amount": "10",
                    }
                ]
            )

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_summary_by_jurisdiction(
                [
                    {
                        "transaction_type": "sale",
                        "vat_amount": "10",
                    }
                ]
            )

    def test_csv_read_and_write_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_path = Path(tmp_dir) / "input.csv"
            out_path = Path(tmp_dir) / "output.csv"

            with in_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "jurisdiction",
                        "transaction_type",
                        "net_amount",
                        "vat_rate",
                        "vat_amount",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "jurisdiction": "NL",
                        "transaction_type": "sale",
                        "net_amount": "100",
                        "vat_rate": "21",
                        "vat_amount": "",
                    }
                )
                writer.writerow(
                    {
                        "jurisdiction": "NL",
                        "transaction_type": "purchase",
                        "net_amount": "",
                        "vat_rate": "",
                        "vat_amount": "5.00",
                    }
                )

            transactions = read_transactions_from_csv(in_path)
            summary = generate_vat_summary_by_jurisdiction(transactions)
            write_summary_to_csv(summary, out_path)

            with out_path.open("r", newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(
                rows,
                [
                    {
                        "jurisdiction": "NL",
                        "output_vat": "21.00",
                        "input_vat": "5.00",
                        "vat_payable": "16.00",
                    }
                ],
            )


if __name__ == "__main__":
    unittest.main()
