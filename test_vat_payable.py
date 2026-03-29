import unittest
from decimal import Decimal

from vat_payable import (
    JurisdictionVatSummary,
    generate_vat_payable_by_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_generates_report_with_mixed_transactions(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "taxable_amount": "100.00",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "taxable_amount": "50",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": "40.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "5",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["DE"],
            JurisdictionVatSummary(
                output_vat=Decimal("19.00"),
                input_vat=Decimal("9.50"),
            ),
        )
        self.assertEqual(result["DE"].vat_payable, Decimal("9.50"))

        self.assertEqual(
            result["FR"],
            JurisdictionVatSummary(
                output_vat=Decimal("40.00"),
                input_vat=Decimal("5.00"),
            ),
        )
        self.assertEqual(result["FR"].vat_payable, Decimal("35.00"))

    def test_accepts_decimal_or_percentage_rates(self) -> None:
        transactions = [
            {
                "jurisdiction": "IE",
                "transaction_type": "sale",
                "taxable_amount": "100",
                "vat_rate": "0.23",
            },
            {
                "jurisdiction": "IE",
                "transaction_type": "sale",
                "taxable_amount": "100",
                "vat_rate": "23",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["IE"].output_vat, Decimal("46.00"))
        self.assertEqual(result["IE"].input_vat, Decimal("0.00"))
        self.assertEqual(result["IE"].vat_payable, Decimal("46.00"))

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "PL",
                        "transaction_type": "refund",
                        "vat_amount": "10",
                    }
                ]
            )

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "transaction_type": "sale",
                        "vat_amount": "10",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
