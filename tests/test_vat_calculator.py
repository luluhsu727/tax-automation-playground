import unittest

from vat_calculator import calculate_vat_to_be_paid_by_jurisdiction


class CalculateVatToBePaidByJurisdictionTests(unittest.TestCase):
    def test_calculates_vat_per_jurisdiction(self):
        transactions = [
            {"jurisdiction": "DE", "vat_type": "output", "vat_amount": 120.50},
            {"jurisdiction": "DE", "vat_type": "input", "vat_amount": 20.50},
            {"jurisdiction": "FR", "vat_type": "output", "vat_amount": 50},
            {"jurisdiction": "FR", "vat_type": "input", "vat_amount": 10},
            {"jurisdiction": "FR", "vat_type": "input", "vat_amount": 5.25},
        ]

        result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {"output_vat": 120.5, "input_vat": 20.5, "vat_payable": 100.0},
                "FR": {"output_vat": 50.0, "input_vat": 15.25, "vat_payable": 34.75},
            },
        )

    def test_returns_negative_vat_payable_when_input_exceeds_output(self):
        transactions = [
            {"jurisdiction": "ES", "vat_type": "output", "vat_amount": 20},
            {"jurisdiction": "ES", "vat_type": "input", "vat_amount": 25},
        ]

        result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result["ES"],
            {"output_vat": 20.0, "input_vat": 25.0, "vat_payable": -5.0},
        )

    def test_raises_for_missing_required_keys(self):
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "DE", "vat_type": "output"}]
            )

    def test_raises_for_invalid_vat_type(self):
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "DE", "vat_type": "sales", "vat_amount": 10}]
            )

    def test_raises_for_negative_vat_amount(self):
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "DE", "vat_type": "output", "vat_amount": -1}]
            )

    def test_raises_for_non_mapping_transaction(self):
        with self.assertRaises(TypeError):
            calculate_vat_to_be_paid_by_jurisdiction(["not-a-dict"])


if __name__ == "__main__":
    unittest.main()
