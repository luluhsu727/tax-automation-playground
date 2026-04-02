import unittest

from vat_calculator import generate_vat_to_be_paid_for_each_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_generates_vat_per_jurisdiction_with_mixed_formats(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": 100},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": 25},
            {"jurisdiction": "FR", "output_vat": 40, "input_vat": 10},
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "amount": 120,
                "vat_rate": 20,
                "is_vat_inclusive": True,
            },
            {
                "jurisdiction": "ES",
                "transaction_type": "purchase",
                "amount": 200,
                "vat_rate": 0.21,
            },
        ]

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": 100.0,
                    "input_vat": 25.0,
                    "vat_payable": 75.0,
                    "position": "payable",
                },
                "ES": {
                    "output_vat": 0.0,
                    "input_vat": 42.0,
                    "vat_payable": -42.0,
                    "position": "refund",
                },
                "FR": {
                    "output_vat": 60.0,
                    "input_vat": 10.0,
                    "vat_payable": 50.0,
                    "position": "payable",
                },
            },
        )

    def test_marks_settled_when_no_balance(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "output_vat": 20, "input_vat": 20},
        ]
        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
        self.assertEqual(result["NL"]["position"], "settled")
        self.assertEqual(result["NL"]["vat_payable"], 0.0)

    def test_raises_for_missing_jurisdiction(self) -> None:
        transactions = [{"transaction_type": "sale", "vat_amount": 10}]
        with self.assertRaisesRegex(ValueError, "missing a valid jurisdiction"):
            generate_vat_to_be_paid_for_each_jurisdiction(transactions)

    def test_raises_for_unsupported_transaction_type(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "transfer", "vat_amount": 10}
        ]
        with self.assertRaisesRegex(ValueError, "unsupported transaction_type"):
            generate_vat_to_be_paid_for_each_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
