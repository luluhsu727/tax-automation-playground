import unittest
from decimal import Decimal

from vat_payable import (
    TransactionVAT,
    calculate_vat_payable_by_jurisdiction,
    row_to_transaction,
)


class VatPayableTests(unittest.TestCase):
    def test_calculates_vat_payable_and_credit(self) -> None:
        transactions = [
            TransactionVAT(jurisdiction="DE", output_vat=Decimal("100.00"), input_vat=Decimal("30.00")),
            TransactionVAT(jurisdiction="DE", output_vat=Decimal("20.00"), input_vat=Decimal("5.00")),
            TransactionVAT(jurisdiction="FR", output_vat=Decimal("25.00"), input_vat=Decimal("40.00")),
        ]

        results = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            results,
            [
                {
                    "jurisdiction": "DE",
                    "output_vat": "120.00",
                    "input_vat": "35.00",
                    "net_vat": "85.00",
                    "vat_to_be_paid": "85.00",
                    "vat_credit_carry_forward": "0.00",
                },
                {
                    "jurisdiction": "FR",
                    "output_vat": "25.00",
                    "input_vat": "40.00",
                    "net_vat": "-15.00",
                    "vat_to_be_paid": "0.00",
                    "vat_credit_carry_forward": "15.00",
                },
            ],
        )

    def test_row_parser_supports_explicit_output_input_vat_columns(self) -> None:
        row = {
            "jurisdiction": "GB",
            "output_vat": "20.25",
            "input_vat": "4.10",
        }
        tx = row_to_transaction(row)
        self.assertEqual(tx.jurisdiction, "GB")
        self.assertEqual(tx.output_vat, Decimal("20.25"))
        self.assertEqual(tx.input_vat, Decimal("4.10"))

    def test_row_parser_supports_vat_amount_and_type_columns(self) -> None:
        output_row = {"jurisdiction": "US-CA", "vat_amount": "12.20", "vat_type": "output"}
        input_row = {"jurisdiction": "US-CA", "vat_amount": "2.20", "vat_type": "input"}

        output_tx = row_to_transaction(output_row)
        input_tx = row_to_transaction(input_row)

        self.assertEqual(output_tx.output_vat, Decimal("12.20"))
        self.assertEqual(output_tx.input_vat, Decimal("0.00"))
        self.assertEqual(input_tx.output_vat, Decimal("0.00"))
        self.assertEqual(input_tx.input_vat, Decimal("2.20"))

    def test_row_parser_supports_taxable_amount_and_rate_columns(self) -> None:
        row = {
            "jurisdiction": "NL",
            "taxable_amount": "199.99",
            "vat_rate": "21",
            "vat_type": "output",
        }
        tx = row_to_transaction(row)
        self.assertEqual(tx.output_vat, Decimal("42.00"))
        self.assertEqual(tx.input_vat, Decimal("0.00"))

    def test_row_parser_rejects_missing_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required jurisdiction"):
            row_to_transaction({"output_vat": "10.00"})


if __name__ == "__main__":
    unittest.main()
