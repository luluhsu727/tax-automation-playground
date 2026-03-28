import unittest

from vat_payable import (
    build_report,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_for_each_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "amount": 1000,
                "vat_rate": 0.19,
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "amount": 100,
                "vat_rate": 0.19,
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "amount": 200,
                "vat_amount": 40,
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "amount": 300,
                "vat_rate": 0.2,
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": 171.0, "FR": -20.0})

    def test_alias_function_returns_same_result(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "transaction_type": "sale",
                "amount": 100,
                "vat_rate": 0.2,
            }
        ]

        self.assertEqual(
            generate_vat_to_be_paid_for_each_jurisdiction(transactions),
            {"UK": 20.0},
        )

    def test_report_shape(self) -> None:
        transactions = [
            {
                "jurisdiction": "NL",
                "transaction_type": "sale",
                "amount": 10,
                "vat_rate": 0.21,
            }
        ]

        self.assertEqual(
            build_report(transactions),
            {"vat_payable_by_jurisdiction": {"NL": 2.1}},
        )

    def test_validation_requires_jurisdiction(self) -> None:
        transactions = [
            {
                "transaction_type": "sale",
                "amount": 100,
                "vat_rate": 0.2,
            }
        ]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_validation_requires_vat_info(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "amount": 100,
            }
        ]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
