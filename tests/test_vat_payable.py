from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vat_payable import (
    Transaction,
    calculate_vat_payable_by_jurisdiction,
    read_transactions_from_csv,
    write_summary_to_csv,
)


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_and_refundable_by_jurisdiction(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("100.00"), Decimal("0.19")),
            Transaction("DE", "purchase", Decimal("40.00"), Decimal("0.19")),
            Transaction("FR", "sale", Decimal("100.00"), Decimal("0.20")),
            Transaction("FR", "purchase", Decimal("150.00"), Decimal("0.20")),
        ]

        summary = calculate_vat_payable_by_jurisdiction(transactions)
        by_jurisdiction = {row.jurisdiction: row for row in summary}

        self.assertEqual(by_jurisdiction["DE"].output_vat, Decimal("19.00"))
        self.assertEqual(by_jurisdiction["DE"].input_vat, Decimal("7.60"))
        self.assertEqual(by_jurisdiction["DE"].net_vat, Decimal("11.40"))
        self.assertEqual(by_jurisdiction["DE"].payable_vat, Decimal("11.40"))
        self.assertEqual(by_jurisdiction["DE"].refundable_vat, Decimal("0.00"))

        self.assertEqual(by_jurisdiction["FR"].output_vat, Decimal("20.00"))
        self.assertEqual(by_jurisdiction["FR"].input_vat, Decimal("30.00"))
        self.assertEqual(by_jurisdiction["FR"].net_vat, Decimal("-10.00"))
        self.assertEqual(by_jurisdiction["FR"].payable_vat, Decimal("0.00"))
        self.assertEqual(by_jurisdiction["FR"].refundable_vat, Decimal("10.00"))

    def test_reads_and_writes_csv(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.csv"
            output_path = tmp_path / "output.csv"
            input_path.write_text(
                "\n".join(
                    [
                        "jurisdiction,transaction_type,net_amount,vat_rate",
                        "DE,sale,100,0.19",
                        "DE,purchase,10,0.19",
                    ]
                ),
                encoding="utf-8",
            )

            transactions = read_transactions_from_csv(input_path)
            summary = calculate_vat_payable_by_jurisdiction(transactions)
            write_summary_to_csv(output_path, summary)

            output_contents = output_path.read_text(encoding="utf-8")
            self.assertIn("jurisdiction,output_vat,input_vat,net_vat,payable_vat,refundable_vat", output_contents)
            self.assertIn("DE,19.00,1.90,17.10,17.10,0.00", output_contents)

    def test_rejects_invalid_transaction_type(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "input.csv"
            input_path.write_text(
                "\n".join(
                    [
                        "jurisdiction,transaction_type,net_amount,vat_rate",
                        "DE,refund,100,0.19",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                read_transactions_from_csv(input_path)


if __name__ == "__main__":
    unittest.main()
