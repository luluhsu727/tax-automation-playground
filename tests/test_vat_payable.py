import unittest

from vat_payable import (
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_calculates_mixed_input_and_output_vat(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": 20,
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "vat_amount": 6,
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": 8.5,
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"DE": 14.0, "FR": 8.5})

    def test_calculates_vat_from_amount_and_rate_percent_or_decimal(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "type": "sales",
                "amount": 120,
                "vat_rate": 20,
            },
            {
                "jurisdiction": "UK",
                "type": "expense",
                "amount": 25,
                "vat_rate": 0.2,
            },
        ]

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
        self.assertEqual(result, {"UK": 19.0})

    def test_skips_zero_totals_by_default_and_can_include_zero(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "type": "sale",
                "vat_amount": 10,
            },
            {
                "jurisdiction": "ES",
                "type": "purchase",
                "vat_amount": 10,
            },
        ]

        default_result = calculate_vat_payable_by_jurisdiction(transactions)
        include_zero_result = calculate_vat_payable_by_jurisdiction(
            transactions, include_zero=True
        )
        self.assertEqual(default_result, {})
        self.assertEqual(include_zero_result, {"ES": 0.0})

    def test_raises_for_missing_jurisdiction(self) -> None:
        transactions = [{"transaction_type": "sale", "vat_amount": 10}]
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_raises_for_missing_vat_fields(self) -> None:
        transactions = [{"jurisdiction": "IT", "type": "sale"}]
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
