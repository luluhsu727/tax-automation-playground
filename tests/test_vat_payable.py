from decimal import Decimal

import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_for_each_jurisdiction(self) -> None:
        rows = [
            {
                "jurisdiction": "UK",
                "transaction_type": "sale",
                "net_amount": "100",
                "vat_rate": "20",
            },
            {
                "jurisdiction": "UK",
                "transaction_type": "purchase",
                "net_amount": "25",
                "vat_rate": "20",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "output",
                "vat_amount": "19.00",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "input",
                "vat_amount": "2.30",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(rows)

        self.assertEqual(
            result,
            {
                "DE": Decimal("16.70"),
                "UK": Decimal("15.00"),
            },
        )

    def test_negative_net_position_is_clamped_to_zero(self) -> None:
        rows = [
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "12.50",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": "5.00",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(rows)

        self.assertEqual(result["FR"], Decimal("0.00"))

    def test_rejects_rows_without_required_amount_fields(self) -> None:
        rows = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "net_amount": "100",
            }
        ]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(rows)


if __name__ == "__main__":
    unittest.main()
