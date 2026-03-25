import unittest
from decimal import Decimal

from vat_payable import (
    VATSummary,
    calculate_transaction_vat,
    generate_vat_payable_by_jurisdiction,
)


class TestCalculateTransactionVAT(unittest.TestCase):
    def test_uses_vat_amount_directly(self) -> None:
        tx = {"vat_amount": "12.345"}
        self.assertEqual(calculate_transaction_vat(tx), Decimal("12.35"))

    def test_computes_from_taxable_amount_and_decimal_rate(self) -> None:
        tx = {"taxable_amount": "100.00", "vat_rate": "0.2"}
        self.assertEqual(calculate_transaction_vat(tx), Decimal("20.00"))

    def test_computes_from_taxable_amount_and_percentage_rate(self) -> None:
        tx = {"taxable_amount": "100.00", "vat_rate": "20"}
        self.assertEqual(calculate_transaction_vat(tx), Decimal("20.00"))

    def test_rejects_missing_vat_inputs(self) -> None:
        tx = {"taxable_amount": "100.00"}
        with self.assertRaises(ValueError):
            calculate_transaction_vat(tx)


class TestGenerateVATPayableByJurisdiction(unittest.TestCase):
    def test_aggregates_output_input_and_payable(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "taxable_amount": 100, "vat_rate": 0.19},
            {"jurisdiction": "DE", "transaction_type": "purchase", "taxable_amount": 20, "vat_rate": 0.19},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "10.00"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "1.25"},
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "0.81"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(set(result.keys()), {"DE", "FR"})
        self.assertIsInstance(result["DE"], VATSummary)
        self.assertEqual(result["DE"].output_vat, Decimal("19.81"))
        self.assertEqual(result["DE"].input_vat, Decimal("3.80"))
        self.assertEqual(result["DE"].vat_payable, Decimal("16.01"))

        self.assertEqual(result["FR"].output_vat, Decimal("10.00"))
        self.assertEqual(result["FR"].input_vat, Decimal("1.25"))
        self.assertEqual(result["FR"].vat_payable, Decimal("8.75"))

    def test_rejects_invalid_transaction_type(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "5.00"},
        ]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_rejects_missing_jurisdiction(self) -> None:
        transactions = [
            {"transaction_type": "sale", "vat_amount": "5.00"},
        ]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
