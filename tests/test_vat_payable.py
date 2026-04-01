import unittest

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_aggregates_existing_vat_amounts_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "vat_amount": "10.25"},
            {"jurisdiction": "DE", "vat_amount": "4.75"},
            {"jurisdiction": "FR", "vat_amount": "8.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": "15.00", "FR": "8.00"})

    def test_calculates_vat_from_taxable_amount_and_rate(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "taxable_amount": "50.00", "vat_rate": "19"},
            {"jurisdiction": "FR", "taxable_amount": "80.00", "vat_rate": "0.20"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": "28.50", "FR": "16.00"})

    def test_rejects_invalid_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction([{"jurisdiction": "", "vat_amount": "10"}])

    def test_requires_rate_when_taxable_amount_is_provided(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "taxable_amount": "100.00"}]
            )


if __name__ == "__main__":
    unittest.main()
