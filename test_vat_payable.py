from decimal import Decimal
import unittest

from vat_payable import VATTransaction, generate_vat_payable_by_jurisdiction


class GenerateVatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_vat_totals_for_multiple_jurisdictions(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19", "transaction_type": "sale"},
            {"jurisdiction": "DE", "amount": "20.00", "vat_rate": "0.19", "transaction_type": "purchase"},
            {"jurisdiction": "FR", "amount": "80.00", "vat_rate": "0.20", "transaction_type": "sale"},
            {"jurisdiction": "FR", "amount": "200.00", "vat_rate": "0.20", "transaction_type": "purchase"},
        ]

        totals = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            totals["DE"],
            {
                "output_vat": Decimal("19.00"),
                "input_vat": Decimal("3.80"),
                "net_vat": Decimal("15.20"),
                "vat_payable": Decimal("15.20"),
                "vat_refundable": Decimal("0.00"),
            },
        )
        self.assertEqual(
            totals["FR"],
            {
                "output_vat": Decimal("16.00"),
                "input_vat": Decimal("40.00"),
                "net_vat": Decimal("-24.00"),
                "vat_payable": Decimal("0.00"),
                "vat_refundable": Decimal("24.00"),
            },
        )

    def test_uses_provided_vat_amount_when_available(self) -> None:
        transactions = [
            VATTransaction(
                jurisdiction="GB",
                amount=Decimal("0.00"),
                vat_rate=Decimal("0.20"),
                transaction_type="sale",
                vat_amount=Decimal("7.35"),
            ),
            VATTransaction(
                jurisdiction="GB",
                amount=Decimal("0.00"),
                vat_rate=Decimal("0.20"),
                transaction_type="purchase",
                vat_amount=Decimal("2.10"),
            ),
        ]

        totals = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(totals["GB"]["vat_payable"], Decimal("5.25"))

    def test_rounds_half_up_to_two_decimals(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "amount": "0.05", "vat_rate": "0.10", "transaction_type": "sale"},
            {"jurisdiction": "ES", "amount": "0.05", "vat_rate": "0.10", "transaction_type": "purchase"},
            {"jurisdiction": "ES", "amount": "0.15", "vat_rate": "0.10", "transaction_type": "sale"},
        ]

        totals = generate_vat_payable_by_jurisdiction(transactions)

        # 0.05 * 0.10 = 0.005 -> 0.01 with ROUND_HALF_UP
        # 0.15 * 0.10 = 0.015 -> 0.02 with ROUND_HALF_UP
        self.assertEqual(totals["ES"]["output_vat"], Decimal("0.03"))
        self.assertEqual(totals["ES"]["input_vat"], Decimal("0.01"))
        self.assertEqual(totals["ES"]["vat_payable"], Decimal("0.02"))

    def test_validates_invalid_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "   ", "amount": "10", "vat_rate": "0.2", "transaction_type": "sale"}]
            )

        with self.assertRaisesRegex(ValueError, "transaction_type"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "IT", "amount": "10", "vat_rate": "0.2", "transaction_type": "refund"}]
            )

        with self.assertRaisesRegex(ValueError, "vat_amount"):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "IT",
                        "amount": "10",
                        "vat_rate": "0.2",
                        "transaction_type": "sale",
                        "vat_amount": "-1.00",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
