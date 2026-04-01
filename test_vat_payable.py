import unittest
from decimal import Decimal

from vat_payable import calculate_vat_payable_by_jurisdiction, vat_payable_json_ready


class VatPayableTests(unittest.TestCase):
    def test_mixed_sales_and_purchases(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "type": "purchase", "amount": "20.00", "vat_rate": "0.19"},
            {"jurisdiction": "FR", "type": "sale", "amount": "80.00", "vat_rate": "0.20"},
        ]

        actual = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(actual["DE"], Decimal("15.20"))
        self.assertEqual(actual["FR"], Decimal("16.00"))

    def test_explicit_vat_fields_take_precedence(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "type": "sale",
                "amount": "9999",
                "vat_rate": "0.99",
                "vat_collected": "50",
                "vat_paid": "15.125",
            }
        ]

        actual = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(actual["UK"], Decimal("34.88"))

    def test_json_ready_output(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "amount": "10", "vat_rate": "0.21"},
            {"jurisdiction": "ES", "type": "purchase", "amount": "5", "vat_rate": "0.21"},
        ]

        actual = vat_payable_json_ready(transactions)
        self.assertEqual(actual, {"ES": "1.05"})

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing 'jurisdiction'"):
            calculate_vat_payable_by_jurisdiction([{"type": "sale", "amount": 10, "vat_rate": 0.2}])

    def test_invalid_type_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "type' of 'sale'/'purchase'"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "amount": 10, "vat_rate": 0.2}]
            )


if __name__ == "__main__":
    unittest.main()
