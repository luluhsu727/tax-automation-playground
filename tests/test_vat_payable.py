import unittest
from decimal import Decimal

from vat_payable import calculate_vat_to_be_paid_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_and_refund_per_jurisdiction(self) -> None:
        records = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": "120.00",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "vat_amount": "20.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "taxable_amount": "100.00",
                "vat_rate": "0.20",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "40.00",
            },
            {
                "jurisdiction": "GB",
                "transaction_type": "sale",
                "vat_amount": "0.00",
            },
        ]

        actual = calculate_vat_to_be_paid_by_jurisdiction(records)

        self.assertEqual(
            actual["DE"],
            {
                "output_vat": Decimal("120.00"),
                "input_vat": Decimal("20.00"),
                "net_vat": Decimal("100.00"),
                "vat_to_be_paid": Decimal("100.00"),
                "refund_due": Decimal("0.00"),
                "status": "payable",
            },
        )
        self.assertEqual(
            actual["FR"],
            {
                "output_vat": Decimal("20.00"),
                "input_vat": Decimal("40.00"),
                "net_vat": Decimal("-20.00"),
                "vat_to_be_paid": Decimal("0.00"),
                "refund_due": Decimal("20.00"),
                "status": "refund_or_zero",
            },
        )
        self.assertEqual(
            actual["GB"],
            {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
                "net_vat": Decimal("0.00"),
                "vat_to_be_paid": Decimal("0.00"),
                "refund_due": Decimal("0.00"),
                "status": "refund_or_zero",
            },
        )

    def test_rounding_and_decimal_places(self) -> None:
        records = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "vat_amount": "10.005",
            },
            {
                "jurisdiction": "ES",
                "transaction_type": "purchase",
                "vat_amount": "5.002",
            },
        ]

        actual = calculate_vat_to_be_paid_by_jurisdiction(records, decimal_places=2)
        self.assertEqual(actual["ES"]["output_vat"], Decimal("10.01"))
        self.assertEqual(actual["ES"]["input_vat"], Decimal("5.00"))
        self.assertEqual(actual["ES"]["vat_to_be_paid"], Decimal("5.01"))

    def test_invalid_transaction_type_raises(self) -> None:
        records = [{"jurisdiction": "DE", "transaction_type": "credit_note", "vat_amount": 1}]

        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid_by_jurisdiction(records)

    def test_missing_amount_definition_raises(self) -> None:
        records = [{"jurisdiction": "DE", "transaction_type": "sale"}]

        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid_by_jurisdiction(records)


if __name__ == "__main__":
    unittest.main()
