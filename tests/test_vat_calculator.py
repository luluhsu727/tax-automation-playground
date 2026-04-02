import unittest
from decimal import Decimal

from vat_calculator import generate_vat_to_be_paid


class VatCalculatorTests(unittest.TestCase):
    def test_calculates_net_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "amount": "1000.00",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "amount": "200.00",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "collected",
                "vat_amount": "120.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "input",
                "vat_amount": "45.50",
            },
        ]

        actual = generate_vat_to_be_paid(transactions)

        self.assertEqual(
            actual,
            {
                "DE": Decimal("152.00"),
                "FR": Decimal("74.50"),
            },
        )

    def test_accepts_fraction_rate(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "transaction_type": "sale",
                "amount": "100.00",
                "vat_rate": "0.20",
            }
        ]

        actual = generate_vat_to_be_paid(transactions)
        self.assertEqual(actual, {"UK": Decimal("20.00")})

    def test_raises_on_unknown_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid(
                [
                    {
                        "jurisdiction": "ES",
                        "transaction_type": "refund",
                        "vat_amount": "10.00",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
