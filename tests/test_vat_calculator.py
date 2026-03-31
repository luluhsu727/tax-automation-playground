import unittest
from decimal import Decimal

from vat_calculator import generate_vat_to_be_paid_for_each_jurisdiction


class TestVatCalculator(unittest.TestCase):
    def test_groups_vat_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "taxable_amount": "100.00"},
            {"jurisdiction": "DE", "taxable_amount": "50.00"},
            {"jurisdiction": "FR", "taxable_amount": "120.00"},
        ]
        vat_rates = {"DE": "0.19", "FR": "0.20"}

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions, vat_rates)

        self.assertEqual(result, {"DE": Decimal("28.50"), "FR": Decimal("24.00")})

    def test_rounds_half_up_per_transaction_to_two_decimal_places(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "taxable_amount": "0.025"},
            {"jurisdiction": "DE", "taxable_amount": "0.025"},
        ]
        vat_rates = {"DE": "0.20"}

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions, vat_rates)

        self.assertEqual(result, {"DE": Decimal("0.02")})

    def test_raises_when_rate_missing_for_jurisdiction(self) -> None:
        transactions = [{"jurisdiction": "ES", "taxable_amount": "100.00"}]
        vat_rates = {"DE": "0.19"}

        with self.assertRaises(ValueError):
            generate_vat_to_be_paid_for_each_jurisdiction(transactions, vat_rates)

    def test_ignores_none_taxable_amount_as_zero(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "taxable_amount": None},
            {"jurisdiction": "DE", "taxable_amount": "100.00"},
        ]
        vat_rates = {"DE": "0.19"}

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions, vat_rates)

        self.assertEqual(result, {"DE": Decimal("19.00")})


if __name__ == "__main__":
    unittest.main()
