import unittest

from vat_calculator import compute_vat_to_be_paid


class VatCalculatorTests(unittest.TestCase):
    def test_compute_vat_to_be_paid_multiple_jurisdictions(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount": 1000,
                "vat_rate": "19%",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount": 200,
                "vat_rate": 0.19,
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "amount": 500,
                "vat_rate": "20%",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "FR",
                "vat_amount": "30.25",
                "transaction_type": "purchase",
            },
        ]

        result = compute_vat_to_be_paid(transactions)

        self.assertEqual(
            result,
            {
                "DE": 152.0,  # 190 - 38
                "FR": 69.75,  # 100 - 30.25
            },
        )

    def test_compute_vat_to_be_paid_allows_negative_balance(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "amount": 100,
                "vat_rate": "21%",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "ES",
                "amount": 300,
                "vat_rate": "21%",
                "transaction_type": "purchase",
            },
        ]

        result = compute_vat_to_be_paid(transactions)
        self.assertEqual(result, {"ES": -42.0})

    def test_compute_vat_to_be_paid_rejects_invalid_transaction_type(self) -> None:
        transactions = [
            {
                "jurisdiction": "IT",
                "amount": 100,
                "vat_rate": "22%",
                "transaction_type": "refund",
            }
        ]

        with self.assertRaises(ValueError) as ctx:
            compute_vat_to_be_paid(transactions)

        self.assertIn("Invalid transaction_type", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
