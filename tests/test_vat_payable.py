from decimal import Decimal
import unittest

from vat_payable import generate_vat_to_be_paid_for_each_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_net_vat_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.19",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "40.00",
                "vat_rate": "0.19",
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "amount_ex_vat": "50.00",
                "vat_rate": "0.20",
                "transaction_type": "sale",
            },
        ]

        actual = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

        self.assertEqual(
            actual,
            {
                "DE": Decimal("11.40"),  # 19.00 - 7.60
                "FR": Decimal("10.00"),
            },
        )

    def test_sorts_output_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "FR",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.20",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.19",
                "transaction_type": "sale",
            },
        ]

        actual = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
        self.assertEqual(list(actual.keys()), ["DE", "FR"])

    def test_raises_for_invalid_transaction_type(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.19",
                "transaction_type": "refund",
            }
        ]

        with self.assertRaisesRegex(ValueError, "Unsupported transaction_type"):
            generate_vat_to_be_paid_for_each_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
