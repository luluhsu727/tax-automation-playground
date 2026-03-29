import unittest
from decimal import Decimal

from src.vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "vat_amount": "100.00"},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": "30.00"},
            {"jurisdiction": "FR", "type": "output", "vat_amount": "80.00"},
            {"jurisdiction": "FR", "type": "input", "vat_amount": "15.00"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("70.00"),
                "FR": Decimal("65.00"),
            },
        )

    def test_uses_transaction_type_alias(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "transaction_type": "sales", "vat_amount": "20"},
            {"jurisdiction": "GB", "transaction_type": "purchases", "vat_amount": "5"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["GB"], Decimal("15.00"))

    def test_returns_negative_when_refundable(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "vat_amount": "10.00"},
            {"jurisdiction": "ES", "type": "purchase", "vat_amount": "25.00"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["ES"], Decimal("-15.00"))

    def test_raises_for_missing_jurisdiction(self) -> None:
        transactions = [{"type": "sale", "vat_amount": "10.00"}]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_raises_for_unknown_transaction_type(self) -> None:
        transactions = [{"jurisdiction": "IT", "type": "adjustment", "vat_amount": "12.00"}]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
