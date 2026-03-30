import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    generate_vat_payable_by_jurisdiction,
    load_transactions_from_csv,
    write_vat_summary_csv,
)


class VatPayableTests(unittest.TestCase):
    def test_generate_summary_from_vat_amount(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "9.50"},
            {"jurisdiction": "FR", "transaction_type": "sales", "vat_amount": "40"},
            {"jurisdiction": "FR", "transaction_type": "expense", "vat_amount": "50.00"},
            {"jurisdiction": "NL", "transaction_type": "output", "vat_amount": "10.00"},
            {"jurisdiction": "NL", "transaction_type": "input", "vat_amount": "10.00"},
        ]

        summary = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(summary["DE"]["output_vat"], Decimal("19.00"))
        self.assertEqual(summary["DE"]["input_vat"], Decimal("9.50"))
        self.assertEqual(summary["DE"]["vat_payable"], Decimal("9.50"))
        self.assertEqual(summary["DE"]["status"], "payable")

        self.assertEqual(summary["FR"]["vat_payable"], Decimal("-10.00"))
        self.assertEqual(summary["FR"]["status"], "refundable")

        self.assertEqual(summary["NL"]["vat_payable"], Decimal("0.00"))
        self.assertEqual(summary["NL"]["status"], "balanced")

    def test_generate_summary_from_amount_and_rate(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": "100.00", "vat_rate": "19"},
            {
                "jurisdiction": "DE",
                "type": "purchase",
                "amount": "50.00",
                "vat_rate": "0.19",
            },
        ]

        summary = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(summary["DE"]["output_vat"], Decimal("19.00"))
        self.assertEqual(summary["DE"]["input_vat"], Decimal("9.50"))
        self.assertEqual(summary["DE"]["vat_payable"], Decimal("9.50"))

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"transaction_type": "sale", "vat_amount": "10.00"}]
            )

    def test_unknown_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "10.00"}]
            )

    def test_csv_load_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_csv = temp_path / "transactions.csv"
            output_csv = temp_path / "summary.csv"

            input_csv.write_text(
                "\n".join(
                    [
                        "jurisdiction,transaction_type,vat_amount",
                        "DE,sale,19.00",
                        "DE,purchase,9.50",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            transactions = load_transactions_from_csv(input_csv)
            summary = generate_vat_payable_by_jurisdiction(transactions)
            write_vat_summary_csv(summary, output_csv)

            output_content = output_csv.read_text(encoding="utf-8")
            self.assertIn(
                "jurisdiction,output_vat,input_vat,vat_payable,status",
                output_content,
            )
            self.assertIn("DE,19.00,9.50,9.50,payable", output_content)


if __name__ == "__main__":
    unittest.main()
