import json
import subprocess
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    Transaction,
    calculate_transaction_vat,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    vat_payable_by_jurisdiction,
)


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generate_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.99"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "10.00"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "4.50"},
        ]
        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
        self.assertEqual(result, {"DE": Decimal("9.99"), "FR": Decimal("4.50")})

    def test_generate_vat_to_be_paid_alias(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "vat_amount": "10.00"},
            {"jurisdiction": "ES", "vat_amount": "5.00"},
            {"jurisdiction": "IT", "vat_amount": "3.00"},
        ]
        result = generate_vat_to_be_paid_by_jurisdiction(transactions)
        self.assertEqual(result, {"ES": Decimal("15.00"), "IT": Decimal("3.00")})

    def test_calculate_vat_payable_by_jurisdiction_with_objects(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("25.00")),
            Transaction("DE", "purchase", Decimal("10.00")),
            Transaction("FR", "sale", Decimal("12.00")),
            Transaction("FR", "purchase", Decimal("20.00")),
        ]
        actual = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(actual["DE"], Decimal("15.00"))
        self.assertEqual(actual["FR"], Decimal("-8.00"))

    def test_generate_vat_payable_structured_summary(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "20.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "3.80"},
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "0.81"},
        ]
        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["DE"].output_vat, Decimal("20.81"))
        self.assertEqual(result["DE"].input_vat, Decimal("3.80"))
        self.assertEqual(result["DE"].vat_payable, Decimal("17.01"))

    def test_calculate_transaction_vat_from_taxable_and_percent_rate(self) -> None:
        vat = calculate_transaction_vat({"taxable_amount": "100.00", "vat_rate": "20"})
        self.assertEqual(vat, Decimal("20.00"))

    def test_alternative_output_input_api(self) -> None:
        records = [
            {"jurisdiction": "DE", "output_vat": 120.0, "input_vat": 20.0},
            {"jurisdiction": "DE", "output_vat": 30.0, "input_vat": 10.0},
            {"jurisdiction": "FR", "output_vat": 50.0, "input_vat": 60.0},
        ]
        result = vat_payable_by_jurisdiction(records)
        self.assertEqual(result, {"DE": 120.0, "FR": 0.0})


class VatPayableCliTests(unittest.TestCase):
    def test_cli_prints_json_result(self) -> None:
        payload = [
            {"jurisdiction": "DE", "output_vat": 25, "input_vat": 5},
            {"jurisdiction": "FR", "output_vat": 30, "input_vat": 9},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "records.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                ["python3", "-m", "vat_payable", str(input_path)],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(json.loads(completed.stdout), {"DE": 20.0, "FR": 21.0})


if __name__ == "__main__":
    unittest.main()
