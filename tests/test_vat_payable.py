import unittest
from decimal import Decimal

from vat_payable import Transaction, compute_vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_computes_output_input_and_payable_per_jurisdiction(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="DE",
                transaction_type="sale",
                amount=Decimal("100"),
                vat_rate=Decimal("0.19"),
            ),
            Transaction(
                jurisdiction="DE",
                transaction_type="purchase",
                amount=Decimal("40"),
                vat_rate=Decimal("0.19"),
            ),
            Transaction(
                jurisdiction="FR",
                transaction_type="sale",
                amount=Decimal("200"),
                vat_rate=Decimal("20"),
            ),
        ]

        summaries = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(summaries["DE"].output_vat, Decimal("19.00"))
        self.assertEqual(summaries["DE"].input_vat, Decimal("7.60"))
        self.assertEqual(summaries["DE"].vat_payable, Decimal("11.40"))

        self.assertEqual(summaries["FR"].output_vat, Decimal("40.00"))
        self.assertEqual(summaries["FR"].input_vat, Decimal("0.00"))
        self.assertEqual(summaries["FR"].vat_payable, Decimal("40.00"))

    def test_supports_amounts_that_already_include_vat(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="GB",
                transaction_type="sale",
                amount=Decimal("120.00"),
                vat_rate=Decimal("0.20"),
                amount_includes_vat=True,
            ),
            Transaction(
                jurisdiction="GB",
                transaction_type="purchase",
                amount=Decimal("24.00"),
                vat_rate=Decimal("0.20"),
                amount_includes_vat=True,
            ),
        ]

        summaries = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(summaries["GB"].output_vat, Decimal("20.00"))
        self.assertEqual(summaries["GB"].input_vat, Decimal("4.00"))
        self.assertEqual(summaries["GB"].vat_payable, Decimal("16.00"))

    def test_rejects_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            compute_vat_payable_by_jurisdiction(
                [
                    Transaction(
                        jurisdiction="ES",
                        transaction_type="refund",
                        amount=Decimal("100"),
                        vat_rate=Decimal("0.21"),
                    )
                ]
            )

    def test_rejects_missing_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            compute_vat_payable_by_jurisdiction(
                [
                    Transaction(
                        jurisdiction=" ",
                        transaction_type="sale",
                        amount=Decimal("50"),
                        vat_rate=Decimal("0.21"),
                    )
                ]
            )


if __name__ == "__main__":
    unittest.main()
