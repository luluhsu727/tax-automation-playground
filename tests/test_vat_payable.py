import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generate_vat_payable_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "190.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "40.25"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "80.00"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "10.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(str(result["DE"]["output_vat"]), "190.00")
        self.assertEqual(str(result["DE"]["input_vat"]), "40.25")
        self.assertEqual(str(result["DE"]["vat_payable"]), "149.75")
        self.assertEqual(str(result["FR"]["vat_payable"]), "70.00")

    def test_can_derive_vat_from_net_amount_and_rate(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "net_amount": "100.00",
                "vat_rate": "0.21",
            },
            {
                "jurisdiction": "ES",
                "transaction_type": "purchase",
                "net_amount": "50.00",
                "vat_rate": "0.21",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(str(result["ES"]["output_vat"]), "21.00")
        self.assertEqual(str(result["ES"]["input_vat"]), "10.50")
        self.assertEqual(str(result["ES"]["vat_payable"]), "10.50")

    def test_raises_on_unsupported_transaction_type(self) -> None:
        transactions = [{"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "1"}]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_cli_json_output(self) -> None:
        csv_content = "\n".join(
            [
                "jurisdiction,transaction_type,vat_amount,net_amount,vat_rate",
                "DE,sale,190.00,,",
                "DE,purchase,40.00,,",
                "FR,sale,,100.00,0.20",
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "transactions.csv"
            csv_path.write_text(csv_content, encoding="utf-8")

            completed = subprocess.run(
                ["python", "vat_payable.py", str(csv_path), "--json"],
                cwd=Path(__file__).resolve().parents[1],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["DE"]["vat_payable"], "150.00")
        self.assertEqual(payload["FR"]["vat_payable"], "20.00")


if __name__ == "__main__":
    unittest.main()
