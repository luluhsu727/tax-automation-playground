import unittest
from decimal import Decimal

from vat_payable import generate_vat_payable_by_jurisdiction


class GenerateVatPayableByJurisdictionTests(unittest.TestCase):
    def test_groups_and_nets_vat_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": "190.00",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "vat_amount": "50.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": "100.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "140.00",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["DE"].output_vat, Decimal("190.00"))
        self.assertEqual(result["DE"].input_vat, Decimal("50.00"))
        self.assertEqual(result["DE"].vat_payable, Decimal("140.00"))

        self.assertEqual(result["FR"].output_vat, Decimal("100.00"))
        self.assertEqual(result["FR"].input_vat, Decimal("140.00"))
        self.assertEqual(result["FR"].vat_payable, Decimal("-40.00"))

    def test_derives_vat_amount_from_taxable_amount_and_rate(self) -> None:
        transactions = [
            {
                "jurisdiction": "GB",
                "transaction_type": "sale",
                "taxable_amount": "200.00",
                "vat_rate": "0.2",
            },
            {
                "jurisdiction": "GB",
                "transaction_type": "purchase",
                "taxable_amount": "50.00",
                "vat_rate": "20",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["GB"].output_vat, Decimal("40.00"))
        self.assertEqual(result["GB"].input_vat, Decimal("10.00"))
        self.assertEqual(result["GB"].vat_payable, Decimal("30.00"))

    def test_rejects_invalid_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "transaction_type"):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "transaction_type": "refund",
                        "vat_amount": "10.00",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
