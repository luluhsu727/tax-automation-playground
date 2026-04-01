import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_and_credit_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "direction": "sale",
                "amount": "1000",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "direction": "purchase",
                "amount": "200",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "FR",
                "direction": "sale",
                "vat_amount": "80",
            },
            {
                "jurisdiction": "FR",
                "direction": "input",
                "vat_amount": "120",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            {
                "DE": {
                    "output_vat": "190.00",
                    "input_vat": "38.00",
                    "net_vat": "152.00",
                    "vat_payable": "152.00",
                    "vat_credit": "0.00",
                },
                "FR": {
                    "output_vat": "80.00",
                    "input_vat": "120.00",
                    "net_vat": "-40.00",
                    "vat_payable": "0.00",
                    "vat_credit": "40.00",
                },
            },
            result,
        )

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty 'jurisdiction'"):
            calculate_vat_payable_by_jurisdiction(
                [{"direction": "sale", "vat_amount": "10"}]
            )

    def test_raises_for_invalid_direction(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid direction"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "GB", "direction": "refund", "vat_amount": "10"}]
            )


if __name__ == "__main__":
    unittest.main()
