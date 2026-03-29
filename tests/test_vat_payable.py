import unittest
from decimal import Decimal

from vat_payable import generate_vat_payable_by_jurisdiction


class GenerateVatPayableByJurisdictionTests(unittest.TestCase):
    def test_aggregates_sales_and_purchases_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "net_amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": "5.25"},
            {"jurisdiction": "FR", "type": "sale", "net_amount": "200", "vat_rate": "20"},
            {"jurisdiction": "FR", "type": "purchase", "net_amount": "50", "vat_rate": "0.20"},
            {"jurisdiction": "DE", "type": "sale", "vat_amount": "1.005"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": Decimal("20.01"),
                    "input_vat": Decimal("5.25"),
                    "vat_payable": Decimal("14.76"),
                },
                "FR": {
                    "output_vat": Decimal("40.00"),
                    "input_vat": Decimal("10.00"),
                    "vat_payable": Decimal("30.00"),
                },
            },
        )

    def test_rejects_unknown_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected 'sale' or 'purchase'"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "vat_amount": 1}]
            )

    def test_requires_vat_input_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "must provide either 'vat_amount'"):
            generate_vat_payable_by_jurisdiction([{"jurisdiction": "DE", "type": "sale"}])

    def test_rejects_negative_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "rate cannot be negative"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "sale", "net_amount": "100", "vat_rate": "-0.19"}]
            )


if __name__ == "__main__":
    unittest.main()
