import unittest
from decimal import Decimal

from vat_report import calculate_vat_by_jurisdiction, vat_to_be_paid_per_jurisdiction


class VATReportTests(unittest.TestCase):
    def test_payable_vat_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "amount": "100", "vat_rate": "19"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "amount": "20", "vat_rate": "19"},
            {"jurisdiction": "FR", "transaction_type": "sale", "amount": "200", "vat_rate": "0.2"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "amount": "210", "vat_rate": "0.2"},
            {"jurisdiction": "UK", "transaction_type": "sale", "vat_amount": "12.50"},
            {"jurisdiction": "UK", "transaction_type": "purchase", "vat_amount": "2.10"},
        ]

        payable = vat_to_be_paid_per_jurisdiction(transactions)

        self.assertEqual(payable["DE"], Decimal("15.2"))
        self.assertEqual(payable["FR"], Decimal("0"))
        self.assertEqual(payable["UK"], Decimal("10.40"))

    def test_summary_includes_reclaimable_vat(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "8"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "12"},
        ]
        summary = calculate_vat_by_jurisdiction(transactions)

        self.assertEqual(summary["FR"].net_vat, Decimal("-4"))
        self.assertEqual(summary["FR"].payable_vat, Decimal("0"))
        self.assertEqual(summary["FR"].reclaimable_vat, Decimal("4"))

    def test_invalid_transaction_type_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_by_jurisdiction(
                [
                    {
                        "jurisdiction": "ES",
                        "transaction_type": "refund",
                        "amount": "100",
                        "vat_rate": "21",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
