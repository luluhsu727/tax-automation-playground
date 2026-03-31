from decimal import Decimal
import unittest

from vat_calculator import generate_vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_groups_and_calculates_payable_vat(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "net_amount": "1000", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": "38.00"},
            {"jurisdiction": "FR", "type": "output", "vat_amount": "120.00"},
            {"jurisdiction": "FR", "type": "input", "net_amount": "200", "vat_rate": "0.2"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": Decimal("190.00"),
                    "input_vat": Decimal("38.00"),
                    "vat_payable": Decimal("152.00"),
                },
                "FR": {
                    "output_vat": Decimal("120.00"),
                    "input_vat": Decimal("40.00"),
                    "vat_payable": Decimal("80.00"),
                },
            },
        )

    def test_negative_payable_results_in_credit(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "type": "sale", "vat_amount": "25.00"},
            {"jurisdiction": "NL", "type": "purchase", "vat_amount": "40.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["NL"]["vat_payable"], Decimal("-15.00"))

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty jurisdiction"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "", "type": "sale", "vat_amount": "10.00"}]
            )

    def test_raises_for_unknown_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Transaction type must be one of"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "vat_amount": "10.00"}]
            )

    def test_raises_when_amount_inputs_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "vat_amount OR both net_amount and vat_rate"):
            generate_vat_payable_by_jurisdiction([{"jurisdiction": "DE", "type": "sale"}])


if __name__ == "__main__":
    unittest.main()
