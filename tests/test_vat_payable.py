import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_with_explicit_vat_amount(self):
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "vat_amount": 120},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": 25},
            {"jurisdiction": "FR", "type": "output", "vat_amount": 10.5},
            {"jurisdiction": "FR", "type": "input", "vat_amount": 2.5},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(
            result,
            {
                "DE": {"output_vat": 120.0, "input_vat": 25.0, "vat_payable": 95.0},
                "FR": {"output_vat": 10.5, "input_vat": 2.5, "vat_payable": 8.0},
            },
        )

    def test_calculates_payable_with_amount_and_rate(self):
        transactions = [
            {"jurisdiction": "UK", "type": "sale", "amount": 100, "vat_rate": 0.2},
            {"jurisdiction": "UK", "type": "expense", "amount": 40, "vat_rate": 0.2},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(
            result,
            {"UK": {"output_vat": 20.0, "input_vat": 8.0, "vat_payable": 12.0}},
        )

    def test_raises_for_unsupported_type(self):
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "vat_amount": 10}]
            )

    def test_raises_for_missing_required_fields(self):
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction([{"type": "sale", "vat_amount": 10}])


if __name__ == "__main__":
    unittest.main()
