import unittest

from vat_calculator import calculate_vat_by_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_generates_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "type": "sale", "amount": 100, "vat_rate": 20},
            {"jurisdiction": "FR", "type": "purchase", "amount": 30, "vat_rate": 20},
            {"jurisdiction": "DE", "type": "sale", "vat_amount": 19.0},
            {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 19},
        ]

        result = calculate_vat_by_jurisdiction(transactions)

        self.assertEqual(
            result["FR"],
            {
                "output_vat": 20.0,
                "input_vat": 6.0,
                "net_vat": 14.0,
                "vat_payable": 14.0,
                "vat_refundable": 0.0,
            },
        )
        self.assertEqual(
            result["DE"],
            {
                "output_vat": 19.0,
                "input_vat": 38.0,
                "net_vat": -19.0,
                "vat_payable": 0.0,
                "vat_refundable": 19.0,
            },
        )

    def test_accepts_fractional_vat_rate(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "type": "sale", "amount": 100, "vat_rate": 0.21},
            {"jurisdiction": "NL", "type": "purchase", "amount": 100, "vat_rate": 0.1},
        ]

        result = calculate_vat_by_jurisdiction(transactions)
        self.assertEqual(result["NL"]["output_vat"], 21.0)
        self.assertEqual(result["NL"]["input_vat"], 10.0)
        self.assertEqual(result["NL"]["vat_payable"], 11.0)

    def test_raises_for_invalid_type(self) -> None:
        transactions = [{"jurisdiction": "FR", "type": "credit_note", "vat_amount": 10}]
        with self.assertRaises(ValueError):
            calculate_vat_by_jurisdiction(transactions)

    def test_raises_when_transaction_cannot_determine_vat(self) -> None:
        transactions = [{"jurisdiction": "FR", "type": "sale", "amount": 100}]
        with self.assertRaises(ValueError):
            calculate_vat_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
