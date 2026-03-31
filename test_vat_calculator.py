import unittest

from vat_calculator import (
    generate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


class VatCalculatorTests(unittest.TestCase):
    def test_generates_vat_position_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
            {"jurisdiction": "FR", "type": "output", "vat_amount": 150},
            {"jurisdiction": "FR", "type": "input", "vat_amount": 200},
            {"jurisdiction": "GB", "type": "sale", "vat_amount": 80},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": 190.0,
                    "input_vat": 38.0,
                    "vat_payable": 152.0,
                    "vat_credit": 0.0,
                },
                "FR": {
                    "output_vat": 150.0,
                    "input_vat": 200.0,
                    "vat_payable": 0.0,
                    "vat_credit": 50.0,
                },
                "GB": {
                    "output_vat": 80.0,
                    "input_vat": 0.0,
                    "vat_payable": 80.0,
                    "vat_credit": 0.0,
                },
            },
        )

    def test_alias_function_matches_primary_function(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "vat_amount": 100},
            {"jurisdiction": "ES", "type": "purchase", "vat_amount": 20},
        ]
        self.assertEqual(
            generate_vat_to_be_paid_for_each_jurisdiction(transactions),
            generate_vat_payable_by_jurisdiction(transactions),
        )

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction([{"type": "sale", "vat_amount": 10}])


if __name__ == "__main__":
    unittest.main()
