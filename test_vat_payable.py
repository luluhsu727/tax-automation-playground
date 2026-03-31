from decimal import Decimal
import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_per_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "net_amount": "100.00",
                "vat_rate": "19",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "net_amount": "50.00",
                "vat_rate": "19",
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "net_amount": "200.00",
                "vat_rate": "0.20",
                "transaction_type": "sale",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["DE"], Decimal("9.50"))
        self.assertEqual(result["FR"], Decimal("40.00"))

    def test_uses_explicit_vat_amount_when_present(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "net_amount": "100.00",
                "vat_rate": "20",
                "transaction_type": "sale",
                "vat_amount": "21.25",
            },
            {
                "jurisdiction": "UK",
                "net_amount": "40.00",
                "vat_rate": "20",
                "transaction_type": "purchase",
                "vat_amount": "8.00",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"UK": Decimal("13.25")})

    def test_validates_required_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "jurisdiction is required"):
            calculate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "",
                        "net_amount": "100.00",
                        "vat_rate": "20",
                        "transaction_type": "sale",
                    }
                ]
            )

        with self.assertRaisesRegex(ValueError, "transaction_type must be either"):
            calculate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "net_amount": "100.00",
                        "vat_rate": "20",
                        "transaction_type": "refund",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
