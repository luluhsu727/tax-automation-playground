import unittest
from decimal import Decimal

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_vat_payable_for_each_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "SG", "transaction_type": "sale", "vat_amount": "10.50"},
            {"jurisdiction": "SG", "transaction_type": "purchase", "vat_amount": "4.25"},
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "20.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "22.00"},
            {"jurisdiction": "US-CA", "transaction_type": "sale", "vat_amount": "2.01"},
        ]

        summaries = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(set(summaries.keys()), {"DE", "SG", "US-CA"})

        self.assertEqual(summaries["SG"].output_vat, Decimal("10.50"))
        self.assertEqual(summaries["SG"].input_vat, Decimal("4.25"))
        self.assertEqual(summaries["SG"].net_vat, Decimal("6.25"))
        self.assertEqual(summaries["SG"].vat_payable, Decimal("6.25"))
        self.assertEqual(summaries["SG"].vat_credit, Decimal("0.00"))

        self.assertEqual(summaries["DE"].net_vat, Decimal("-2.00"))
        self.assertEqual(summaries["DE"].vat_payable, Decimal("0.00"))
        self.assertEqual(summaries["DE"].vat_credit, Decimal("2.00"))

    def test_supports_amount_times_rate_when_vat_amount_missing(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "transaction_type": "sale", "amount": "100", "vat_rate": "0.20"},
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "amount": "30.00",
                "vat_rate": "0.20",
            },
        ]

        summary = generate_vat_payable_by_jurisdiction(transactions)["FR"]

        self.assertEqual(summary.output_vat, Decimal("20.00"))
        self.assertEqual(summary.input_vat, Decimal("6.00"))
        self.assertEqual(summary.vat_payable, Decimal("14.00"))

    def test_rounds_half_up_to_two_decimal_places(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "transaction_type": "sale", "vat_amount": "1.005"},
            {"jurisdiction": "GB", "transaction_type": "purchase", "vat_amount": "0.000"},
        ]
        summary = generate_vat_payable_by_jurisdiction(transactions)["GB"]
        self.assertEqual(summary.output_vat, Decimal("1.01"))

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "SG", "transaction_type": "refund", "vat_amount": "1.00"}]
            )

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"transaction_type": "sale", "vat_amount": "1.00"}]
            )


if __name__ == "__main__":
    unittest.main()
