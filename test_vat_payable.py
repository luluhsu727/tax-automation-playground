import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generate_vat_payable_groups_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "120.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "20.00"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "40.50"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "70.10"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["DE"],
            {
                "output_vat": Decimal("120.00"),
                "input_vat": Decimal("20.00"),
                "net_vat": Decimal("100.00"),
                "vat_payable": Decimal("100.00"),
                "vat_refundable": Decimal("0.00"),
            },
        )
        self.assertEqual(
            result["FR"],
            {
                "output_vat": Decimal("40.50"),
                "input_vat": Decimal("70.10"),
                "net_vat": Decimal("-29.60"),
                "vat_payable": Decimal("0.00"),
                "vat_refundable": Decimal("29.60"),
            },
        )

    def test_generate_vat_from_net_amount_and_rate(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "transaction_type": "sale", "net_amount": "100", "vat_rate": "0.21"},
            {"jurisdiction": "ES", "transaction_type": "purchase", "net_amount": "50", "vat_rate": "21"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["ES"]["output_vat"], Decimal("21.00"))
        self.assertEqual(result["ES"]["input_vat"], Decimal("10.50"))
        self.assertEqual(result["ES"]["vat_payable"], Decimal("10.50"))

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "5"}]
            )

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "transactions.csv"
            csv_path.write_text(
                (
                    "jurisdiction,transaction_type,vat_amount\n"
                    "DE,sale,19.99\n"
                    "DE,purchase,10.00\n"
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [sys.executable, "vat_payable.py", str(csv_path)],
                cwd=Path(__file__).resolve().parent,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["DE"]["vat_payable"], "9.99")
            self.assertEqual(payload["DE"]["vat_refundable"], "0.00")


if __name__ == "__main__":
    unittest.main()
