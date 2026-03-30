from decimal import Decimal
import unittest

from vat import (
    calculate_vat_payable_by_jurisdiction,
    calculate_vat_summary_by_jurisdiction,
    generate_vat_payable_for_each_jurisdiction,
)


class VatCalculationTests(unittest.TestCase):
    def test_summary_by_jurisdiction_mixed_transactions(self) -> None:
        transactions = [
            {"jurisdiction": "de", "type": "sale", "amount": 1000, "vat_rate": 0.19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 300, "vat_rate": 0.19},
            {"jurisdiction": "FR", "direction": "output", "vat_amount": "200.00"},
            {"jurisdiction": "FR", "direction": "input", "vat_amount": "80.00"},
            {"jurisdiction": "FR", "type": "purchase", "vat_amount": "20.00", "recoverable": False},
        ]

        result = calculate_vat_summary_by_jurisdiction(transactions)

        self.assertEqual(result["DE"]["output_vat"], Decimal("190.0"))
        self.assertEqual(result["DE"]["input_vat"], Decimal("57.0"))
        self.assertEqual(result["DE"]["net_vat"], Decimal("133.0"))

        self.assertEqual(result["FR"]["output_vat"], Decimal("200.00"))
        self.assertEqual(result["FR"]["input_vat"], Decimal("80.00"))
        self.assertEqual(result["FR"]["net_vat"], Decimal("120.00"))

    def test_vat_payable_clamps_negative_balances(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 300, "vat_rate": 0.19},
            {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
            {"jurisdiction": "FR", "type": "purchase", "amount": 700, "vat_rate": 0.20},
        ]

        result = generate_vat_payable_for_each_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("133.00"),
                "FR": Decimal("0.00"),
            },
        )

    def test_can_return_negative_net_when_not_clamped(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "amount": 100, "vat_rate": 0.21},
            {"jurisdiction": "ES", "type": "purchase", "amount": 300, "vat_rate": 0.21},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions, clamp_negative=False)
        self.assertEqual(result["ES"], Decimal("-42.00"))

    def test_missing_required_fields_raise(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_summary_by_jurisdiction([{"type": "sale", "vat_amount": 10}])

        with self.assertRaises(ValueError):
            calculate_vat_summary_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "sale", "amount": 100}]
            )


if __name__ == "__main__":
    unittest.main()
