import unittest

from vat_calculator import calculate_vat_payable_by_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_calculates_vat_from_net_and_rate(self):
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "net_amount": "100.00",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "net_amount": "20.00",
                "vat_rate": "0.19",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"DE": "15.20"})

    def test_aggregates_multiple_jurisdictions(self):
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "3.80"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "20.00"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "30.00"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"DE": "15.20", "FR": "-10.00"})

    def test_accepts_output_and_input_aliases(self):
        transactions = [
            {"jurisdiction": "IT", "transaction_type": "output", "vat_amount": "22.00"},
            {"jurisdiction": "IT", "transaction_type": "input", "vat_amount": "2.00"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"IT": "20.00"})

    def test_rejects_invalid_transaction_type(self):
        transactions = [{"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "1.00"}]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_rejects_missing_jurisdiction(self):
        transactions = [{"transaction_type": "sale", "vat_amount": "10.00"}]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)

    def test_rejects_missing_vat_fields(self):
        transactions = [{"jurisdiction": "DE", "transaction_type": "sale"}]

        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
