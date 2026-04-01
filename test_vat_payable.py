from decimal import Decimal
import unittest

from vat_payable import JurisdictionVatSummary, generate_vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "5.00"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "10.00"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "14.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["DE"],
            JurisdictionVatSummary(
                output_vat=Decimal("19.00"),
                input_vat=Decimal("5.00"),
                vat_payable=Decimal("14.00"),
            ),
        )
        self.assertEqual(
            result["FR"],
            JurisdictionVatSummary(
                output_vat=Decimal("10.00"),
                input_vat=Decimal("14.00"),
                vat_payable=Decimal("-4.00"),
            ),
        )

    def test_uses_net_amount_and_rate_when_vat_missing(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "transaction_type": "sale", "net_amount": "100", "vat_rate": "0.20"},
            {"jurisdiction": "GB", "transaction_type": "purchase", "net_amount": "20", "vat_rate": "0.20"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        gb = result["GB"]

        self.assertEqual(gb.output_vat, Decimal("20.00"))
        self.assertEqual(gb.input_vat, Decimal("4.00"))
        self.assertEqual(gb.vat_payable, Decimal("16.00"))

    def test_can_clamp_negative_payable(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "transaction_type": "sale", "vat_amount": "3.00"},
            {"jurisdiction": "ES", "transaction_type": "purchase", "vat_amount": "8.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(
            transactions,
            clamp_negative_payable=True,
        )

        self.assertEqual(result["ES"].vat_payable, Decimal("0.00"))

    def test_raises_for_invalid_transaction_type(self) -> None:
        transactions = [
            {"jurisdiction": "IT", "transaction_type": "refund", "vat_amount": "2.00"}
        ]

        with self.assertRaisesRegex(ValueError, "invalid transaction_type"):
            generate_vat_payable_by_jurisdiction(transactions)

    def test_raises_when_missing_vat_and_net_rate(self) -> None:
        transactions = [
            {"jurisdiction": "IT", "transaction_type": "sale", "net_amount": "10.00"}
        ]

        with self.assertRaisesRegex(ValueError, "vat_rate"):
            generate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
