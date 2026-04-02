import unittest
from decimal import Decimal

from vat_payable.calculator import (
    Transaction,
    VatComputationError,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid,
)


class VatCalculatorTests(unittest.TestCase):
    def test_calculates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            Transaction(jurisdiction="DE", amount=1000, vat_rate=0.19, transaction_type="sale"),
            Transaction(jurisdiction="DE", amount=200, vat_rate=0.19, transaction_type="purchase"),
            Transaction(jurisdiction="FR", amount=500, vat_rate=0.20, transaction_type="sale"),
            Transaction(jurisdiction="FR", amount=300, vat_rate=0.20, transaction_type="purchase"),
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["DE"]["output_vat"], 190.0)
        self.assertEqual(result["DE"]["input_vat"], 38.0)
        self.assertEqual(result["DE"]["vat_to_be_paid"], 152.0)
        self.assertEqual(result["DE"]["vat_payable"], 152.0)

        self.assertEqual(result["FR"]["output_vat"], 100.0)
        self.assertEqual(result["FR"]["input_vat"], 60.0)
        self.assertEqual(result["FR"]["vat_to_be_paid"], 40.0)
        self.assertEqual(result["FR"]["vat_payable"], 40.0)

    def test_supports_explicit_vat_amount(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="ES",
                amount=1000,
                vat_rate=0.21,
                transaction_type="sale",
                vat_amount=150,
            )
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["ES"]["output_vat"], 150.0)
        self.assertEqual(result["ES"]["vat_to_be_paid"], 150.0)

    def test_supports_percentage_vat_rate(self) -> None:
        transactions = [Transaction(jurisdiction="IT", amount=100, vat_rate=22, transaction_type="sale")]
        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["IT"]["output_vat"], 22.0)

    def test_raises_for_invalid_transaction_type(self) -> None:
        transactions = [
            Transaction(jurisdiction="DE", amount=100, vat_rate=0.19, transaction_type="refund")
        ]

        with self.assertRaises(VatComputationError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_generate_vat_to_be_paid_returns_decimals(self) -> None:
        result = generate_vat_to_be_paid(
            [
                Transaction(jurisdiction="NL", amount="50", vat_rate="0.21", transaction_type="sale"),
                Transaction(jurisdiction="NL", vat_amount="2.10", transaction_type="purchase"),
            ]
        )

        self.assertEqual(result["NL"].output_vat, Decimal("10.50"))
        self.assertEqual(result["NL"].input_vat, Decimal("2.10"))
        self.assertEqual(result["NL"].vat_to_be_paid, Decimal("8.40"))


if __name__ == "__main__":
    unittest.main()
