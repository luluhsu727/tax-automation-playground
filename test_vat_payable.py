import unittest

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_payable_and_credit_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "output_vat": "190.00", "input_vat": "50.00"},
            {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "FR", "output_vat": "50.00", "input_vat": "60.00"},
            {"jurisdiction": "FR", "output_vat": "20.00", "input_vat": "5.00"},
            {"jurisdiction": "NL", "taxable_amount": "200.00", "vat_rate": "0.21"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["jurisdictions"],
            [
                {
                    "jurisdiction": "DE",
                    "output_vat": "209.00",
                    "input_vat": "50.00",
                    "net_vat": "159.00",
                    "vat_payable": "159.00",
                    "vat_credit": "0.00",
                },
                {
                    "jurisdiction": "FR",
                    "output_vat": "70.00",
                    "input_vat": "65.00",
                    "net_vat": "5.00",
                    "vat_payable": "5.00",
                    "vat_credit": "0.00",
                },
                {
                    "jurisdiction": "NL",
                    "output_vat": "42.00",
                    "input_vat": "0.00",
                    "net_vat": "42.00",
                    "vat_payable": "42.00",
                    "vat_credit": "0.00",
                },
            ],
        )
        self.assertEqual(
            result["totals"],
            {
                "output_vat": "321.00",
                "input_vat": "115.00",
                "net_vat": "206.00",
                "vat_payable": "206.00",
                "vat_credit": "0.00",
            },
        )

    def test_captures_credit_when_input_exceeds_output(self) -> None:
        transactions = [{"jurisdiction": "ES", "output_vat": "10.00", "input_vat": "25.00"}]
        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["jurisdictions"][0],
            {
                "jurisdiction": "ES",
                "output_vat": "10.00",
                "input_vat": "25.00",
                "net_vat": "-15.00",
                "vat_payable": "0.00",
                "vat_credit": "15.00",
            },
        )
        self.assertEqual(
            result["totals"],
            {
                "output_vat": "10.00",
                "input_vat": "25.00",
                "net_vat": "-15.00",
                "vat_payable": "0.00",
                "vat_credit": "15.00",
            },
        )

    def test_requires_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction([{"output_vat": "10.00"}])


if __name__ == "__main__":
    unittest.main()
