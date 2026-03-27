import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal

from vat_calculator import generate_vat_payable_by_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_generates_payable_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
            {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
            {"jurisdiction": "FR", "type": "purchase", "amount": 100, "vat_rate": 0.20},
        ]

        vat_payable = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(vat_payable["DE"], Decimal("152.00"))
        self.assertEqual(vat_payable["FR"], Decimal("80.00"))

    def test_purchase_only_results_in_negative_payable(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "purchase", "amount": 100, "vat_rate": 0.21},
        ]

        vat_payable = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(vat_payable["ES"], Decimal("-21.00"))

    def test_unknown_transaction_type_raises(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "refund", "amount": 10, "vat_rate": 0.19},
        ]

        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_cli_outputs_json(self) -> None:
        transactions = [
            {"jurisdiction": "IT", "type": "sale", "amount": 50, "vat_rate": 0.22},
            {"jurisdiction": "IT", "type": "purchase", "amount": 10, "vat_rate": 0.22},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as file:
            json.dump(transactions, file)
            file.flush()
            command = [sys.executable, "vat_calculator.py", "--input", file.name]
            output = subprocess.check_output(command, text=True)

        payload = json.loads(output)
        self.assertEqual(payload, {"IT": "8.80"})


if __name__ == "__main__":
    unittest.main()
