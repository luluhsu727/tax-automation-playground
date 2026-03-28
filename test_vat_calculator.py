import unittest

from vat_calculator import generate_vat_payable_by_jurisdiction


class GenerateVatPayableByJurisdictionTests(unittest.TestCase):
    def test_groups_totals_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "amount": "100",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "amount": "40",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "output",
                "vat_amount": "15.5",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "input",
                "vat_amount": "10.0",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": 11.4, "FR": 5.5})

    def test_accepts_percentage_rate_over_one(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "transaction_type": "sale",
                "amount": 250,
                "vat_rate": 20,
            }
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"UK": 50.0})

    def test_supports_precision_configuration(self) -> None:
        transactions = [
            {
                "jurisdiction": "NL",
                "transaction_type": "sale",
                "amount": "100",
                "vat_rate": "0.21234",
            }
        ]

        result = generate_vat_payable_by_jurisdiction(transactions, precision=3)

        self.assertEqual(result, {"NL": 21.234})

    def test_raises_for_missing_jurisdiction(self) -> None:
        transactions = [{"transaction_type": "sale", "amount": 100, "vat_rate": 0.2}]

        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_raises_for_invalid_transaction_type(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "refund",
                "amount": 100,
                "vat_rate": 0.19,
            }
        ]

        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
