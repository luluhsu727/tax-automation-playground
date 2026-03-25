import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_calculates_output_minus_input_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "net_amount": "1000.00", "vat_rate": "0.19", "transaction_type": "sale"},
            {"jurisdiction": "DE", "net_amount": "200.00", "vat_rate": "0.19", "transaction_type": "purchase"},
            {"jurisdiction": "FR", "net_amount": "500.00", "vat_rate": "0.20", "transaction_type": "sale"},
            {"jurisdiction": "FR", "net_amount": "150.00", "vat_rate": "0.20", "transaction_type": "purchase"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {"output_vat": "190.00", "input_vat": "38.00", "vat_payable": "152.00"},
                "FR": {"output_vat": "100.00", "input_vat": "30.00", "vat_payable": "70.00"},
            },
        )

    def test_uses_explicit_vat_amount_when_present(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "net_amount": "100.00",
                "vat_rate": "0.21",
                "transaction_type": "sale",
                "vat_amount": "20.00",
            },
            {
                "jurisdiction": "ES",
                "net_amount": "10.00",
                "vat_rate": "0.21",
                "transaction_type": "purchase",
                "vat_amount": "2.10",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["ES"],
            {"output_vat": "20.00", "input_vat": "2.10", "vat_payable": "17.90"},
        )

    def test_rejects_invalid_transaction_type(self) -> None:
        transactions = [
            {"jurisdiction": "IT", "net_amount": "100.00", "vat_rate": "0.22", "transaction_type": "refund"},
        ]

        with self.assertRaisesRegex(ValueError, "transaction_type must be either 'sale' or 'purchase'"):
            calculate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
