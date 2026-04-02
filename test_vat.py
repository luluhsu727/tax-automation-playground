import unittest

from vat import (
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
)


class VatByJurisdictionTests(unittest.TestCase):
    def test_calculates_net_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "vat_amount": 19},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": 7.5},
            {"jurisdiction": "FR", "type": "output", "vat_amount": 20},
            {"jurisdiction": "FR", "type": "input", "vat_amount": 9},
            {"jurisdiction": "DE", "type": "output", "vat_amount": 2.25},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": 13.75, "FR": 11.0})

    def test_uses_amount_and_rate_when_vat_amount_missing(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "type": "sale", "amount": 100, "vat_rate": 0.21},
            {
                "jurisdiction": "NL",
                "type": "purchase",
                "amount": 40,
                "vat_rate": 0.21,
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"NL": 12.6})

    def test_accepts_alternate_type_field_names(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "transaction_type": "sale", "vat_amount": 15},
            {"jurisdiction": "ES", "direction": "purchase", "vat_amount": 3},
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(result, {"ES": 12.0})

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction([{"type": "sale", "vat_amount": 1}])

    def test_raises_for_unknown_type(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "US", "type": "refund", "vat_amount": 1}]
            )


if __name__ == "__main__":
    unittest.main()
