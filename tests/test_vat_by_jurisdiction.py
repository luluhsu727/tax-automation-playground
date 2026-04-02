import unittest

from vat_by_jurisdiction import generate_vat_payable_by_jurisdiction


class VatByJurisdictionTests(unittest.TestCase):
    def test_generates_payable_and_credit_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "vat_amount": 120.00},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": 30.00},
            {"jurisdiction": "FR", "type": "output", "vat_amount": 40.00},
            {"jurisdiction": "FR", "type": "input", "vat_amount": 52.00},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            {
                "DE": {
                    "output_vat": 120.0,
                    "input_vat": 30.0,
                    "vat_payable": 90.0,
                    "vat_credit": 0.0,
                },
                "FR": {
                    "output_vat": 40.0,
                    "input_vat": 52.0,
                    "vat_payable": 0.0,
                    "vat_credit": 12.0,
                },
            },
            result,
        )

    def test_derives_vat_from_amount_and_rate_with_rounding(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "amount": "10.005", "vat_rate": "0.2"},
            {"jurisdiction": "ES", "type": "purchase", "amount": 5, "vat_rate": 0.2},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(2.0, result["ES"]["output_vat"])
        self.assertEqual(1.0, result["ES"]["input_vat"])
        self.assertEqual(1.0, result["ES"]["vat_payable"])
        self.assertEqual(0.0, result["ES"]["vat_credit"])

    def test_rejects_negative_vat(self) -> None:
        transactions = [{"jurisdiction": "IT", "type": "sale", "vat_amount": -1}]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_requires_supported_transaction_type(self) -> None:
        transactions = [{"jurisdiction": "NL", "type": "refund", "vat_amount": 10}]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_requires_vat_input(self) -> None:
        transactions = [{"jurisdiction": "PL", "type": "sale", "amount": 100}]
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
