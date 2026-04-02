import unittest
from decimal import Decimal

from vat import calculate_vat_payable_by_jurisdiction


class TestCalculateVatPayableByJurisdiction(unittest.TestCase):
    def test_aggregates_mixed_input_styles(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "vat_amount": "1.50"},
            {"jurisdiction": "FR", "amount": "50", "vat_rate": "0.2"},
            {"jurisdiction": "FR", "vat_amount": "0.015"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("20.50"),
                "FR": Decimal("10.02"),
            },
        )

    def test_supports_custom_rounding_precision(self) -> None:
        transactions = [
            {"jurisdiction": "SE", "vat_amount": "12.3456"},
            {"jurisdiction": "SE", "vat_amount": "0.0004"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions, decimal_places=3)
        self.assertEqual(result, {"SE": Decimal("12.346")})

    def test_raises_for_missing_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction([{"jurisdiction": "GB", "amount": "10"}])

    def test_raises_for_empty_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction([{"jurisdiction": " ", "vat_amount": "1"}])


if __name__ == "__main__":
    unittest.main()
