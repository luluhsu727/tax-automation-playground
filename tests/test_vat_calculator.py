import unittest
from decimal import Decimal

from vat_calculator import generate_vat_payable_by_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_generates_net_payable_and_reclaimable_per_jurisdiction(self):
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
            {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
            {"jurisdiction": "FR", "type": "purchase", "amount": 700, "vat_rate": 0.20},
            {"jurisdiction": "UK", "type": "purchase", "amount": 150, "vat_rate": 0.20},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["DE"]["output_vat"], Decimal("190.00"))
        self.assertEqual(result["DE"]["input_vat"], Decimal("38.00"))
        self.assertEqual(result["DE"]["net_vat"], Decimal("152.00"))
        self.assertEqual(result["DE"]["vat_payable"], Decimal("152.00"))
        self.assertEqual(result["DE"]["vat_reclaimable"], Decimal("0.00"))

        self.assertEqual(result["FR"]["output_vat"], Decimal("100.00"))
        self.assertEqual(result["FR"]["input_vat"], Decimal("140.00"))
        self.assertEqual(result["FR"]["net_vat"], Decimal("-40.00"))
        self.assertEqual(result["FR"]["vat_payable"], Decimal("0.00"))
        self.assertEqual(result["FR"]["vat_reclaimable"], Decimal("40.00"))

        self.assertEqual(result["UK"]["output_vat"], Decimal("0.00"))
        self.assertEqual(result["UK"]["input_vat"], Decimal("30.00"))
        self.assertEqual(result["UK"]["net_vat"], Decimal("-30.00"))
        self.assertEqual(result["UK"]["vat_payable"], Decimal("0.00"))
        self.assertEqual(result["UK"]["vat_reclaimable"], Decimal("30.00"))

    def test_explicit_vat_amount_overrides_rate_and_amount(self):
        transactions = [
            {
                "jurisdiction": "ES",
                "type": "sale",
                "amount": 9999,
                "vat_rate": 0.21,
                "vat_amount": 50,
            },
            {
                "jurisdiction": "ES",
                "type": "purchase",
                "amount": 100,
                "vat_rate": 0.21,
                "vat_amount": 12.5,
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["ES"]["output_vat"], Decimal("50.00"))
        self.assertEqual(result["ES"]["input_vat"], Decimal("12.50"))
        self.assertEqual(result["ES"]["vat_payable"], Decimal("37.50"))

    def test_raises_error_for_missing_required_fields(self):
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"type": "sale", "amount": 100, "vat_rate": 0.2}]
            )

    def test_raises_error_for_invalid_type(self):
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "amount": 100, "vat_rate": 0.2}]
            )


if __name__ == "__main__":
    unittest.main()
