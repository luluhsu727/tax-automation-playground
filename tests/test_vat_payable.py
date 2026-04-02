import unittest
from decimal import Decimal

from vat_payable import Transaction, calculate_vat_payable_by_jurisdiction, format_results


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_for_single_jurisdiction(self) -> None:
        transactions = [
            Transaction.from_dict(
                {
                    "jurisdiction": "DE",
                    "transaction_type": "sale",
                    "amount": "100.00",
                    "vat_rate": "0.19",
                }
            ),
            Transaction.from_dict(
                {
                    "jurisdiction": "DE",
                    "transaction_type": "purchase",
                    "amount": "20.00",
                    "vat_rate": "0.19",
                }
            ),
        ]

        totals = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(totals["DE"]["output_vat"], Decimal("19.00"))
        self.assertEqual(totals["DE"]["input_vat"], Decimal("3.80"))
        self.assertEqual(totals["DE"]["vat_payable"], Decimal("15.20"))

    def test_uses_explicit_vat_amount_when_provided(self) -> None:
        transactions = [
            Transaction.from_dict(
                {
                    "jurisdiction": "FR",
                    "transaction_type": "sale",
                    "amount": "100.00",
                    "vat_rate": "0.20",
                    "vat_amount": "17.00",
                }
            ),
            Transaction.from_dict(
                {
                    "jurisdiction": "FR",
                    "transaction_type": "purchase",
                    "amount": "30.00",
                    "vat_rate": "0.20",
                }
            ),
        ]

        totals = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(totals["FR"]["output_vat"], Decimal("17.00"))
        self.assertEqual(totals["FR"]["input_vat"], Decimal("6.00"))
        self.assertEqual(totals["FR"]["vat_payable"], Decimal("11.00"))

    def test_groups_totals_by_jurisdiction(self) -> None:
        transactions = [
            Transaction.from_dict(
                {
                    "jurisdiction": "UK",
                    "transaction_type": "sale",
                    "amount": "50.00",
                    "vat_rate": "0.20",
                }
            ),
            Transaction.from_dict(
                {
                    "jurisdiction": "ES",
                    "transaction_type": "sale",
                    "amount": "100.00",
                    "vat_rate": "0.21",
                }
            ),
            Transaction.from_dict(
                {
                    "jurisdiction": "ES",
                    "transaction_type": "purchase",
                    "amount": "200.00",
                    "vat_rate": "0.21",
                }
            ),
        ]

        totals = calculate_vat_payable_by_jurisdiction(transactions)
        formatted = format_results(totals)

        self.assertEqual(formatted["UK"]["vat_payable"], "10.00")
        self.assertEqual(formatted["ES"]["output_vat"], "21.00")
        self.assertEqual(formatted["ES"]["input_vat"], "42.00")
        self.assertEqual(formatted["ES"]["vat_payable"], "-21.00")

    def test_requires_vat_rate_or_vat_amount(self) -> None:
        with self.assertRaises(ValueError):
            Transaction.from_dict(
                {
                    "jurisdiction": "IT",
                    "transaction_type": "sale",
                    "amount": "100.00",
                }
            )


if __name__ == "__main__":
    unittest.main()
