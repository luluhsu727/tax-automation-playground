import unittest

from vat_payable import generate_vat_to_be_paid_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "taxable_amount": 1000,
                "vat_rate": 0.19,
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "taxable_amount": 500,
                "vat_rate": 0.19,
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "taxable_amount": 2000,
                "vat_rate": 0.2,
                "transaction_type": "sales",
            },
            {
                "jurisdiction": "FR",
                "taxable_amount": 2100,
                "vat_rate": 0.2,
                "transaction_type": "input",
            },
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": 190.0,
                    "input_vat": 95.0,
                    "vat_to_be_paid": 95.0,
                    "vat_credit": 0.0,
                },
                "FR": {
                    "output_vat": 400.0,
                    "input_vat": 420.0,
                    "vat_to_be_paid": 0.0,
                    "vat_credit": 20.0,
                },
            },
        )

    def test_rounds_to_two_decimals(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "taxable_amount": 99.999,
                "vat_rate": 0.21,
                "transaction_type": "output",
            }
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(result["ES"]["output_vat"], 21.0)
        self.assertEqual(result["ES"]["vat_to_be_paid"], 21.0)

    def test_raises_for_missing_required_fields(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "DE", "taxable_amount": 100}]
            )

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "taxable_amount": 100,
                        "vat_rate": 0.19,
                        "transaction_type": "refund",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
