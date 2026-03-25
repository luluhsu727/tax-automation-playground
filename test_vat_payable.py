from decimal import Decimal
import unittest

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "taxable_amount": "100", "vat_rate": "19"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "taxable_amount": "20", "vat_rate": "19"},
            {"jurisdiction": "FR", "transaction_type": "output", "vat_amount": "40.00"},
            {"jurisdiction": "FR", "transaction_type": "input", "vat_amount": "55.00"},
            {"jurisdiction": "DE", "transaction_type": "expense", "vat_amount": "1.90"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            [
                {
                    "jurisdiction": "DE",
                    "output_vat": Decimal("19.00"),
                    "input_vat": Decimal("5.70"),
                    "net_vat": Decimal("13.30"),
                    "vat_payable": Decimal("13.30"),
                    "vat_refundable": Decimal("0.00"),
                },
                {
                    "jurisdiction": "FR",
                    "output_vat": Decimal("40.00"),
                    "input_vat": Decimal("55.00"),
                    "net_vat": Decimal("-15.00"),
                    "vat_payable": Decimal("0.00"),
                    "vat_refundable": Decimal("15.00"),
                },
            ],
        )

    def test_accepts_decimal_rate(self) -> None:
        transactions = [
            {"jurisdiction": "SG", "transaction_type": "sales", "taxable_amount": "1000", "vat_rate": "0.09"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result[0]["vat_payable"], Decimal("90.00"))

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "GB",
                        "transaction_type": "transfer",
                        "vat_amount": "1.00",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
