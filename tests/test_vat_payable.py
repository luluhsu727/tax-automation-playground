import unittest

from vat_payable import calculate_vat_by_jurisdiction, parse_rate_flags


class VatPayableTests(unittest.TestCase):
    def test_calculates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "kind": "sale", "amount": "1000", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "kind": "purchase", "amount": "100", "vat_rate": "0.19"},
            {"jurisdiction": "FR", "kind": "sale", "amount": "500", "vat_rate": "0.20"},
            {"jurisdiction": "FR", "kind": "purchase", "amount": "50", "vat_rate": "0.20"},
        ]

        result = calculate_vat_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {"output_vat": 190.0, "input_vat": 19.0, "vat_payable": 171.0},
                "FR": {"output_vat": 100.0, "input_vat": 10.0, "vat_payable": 90.0},
            },
        )

    def test_uses_default_rate_when_not_on_transaction(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "kind": "sale", "amount": "120.00"},
            {"jurisdiction": "ES", "kind": "purchase", "amount": "20.00"},
        ]

        result = calculate_vat_by_jurisdiction(transactions, {"ES": 0.21})

        self.assertEqual(
            result["ES"],
            {"output_vat": 25.2, "input_vat": 4.2, "vat_payable": 21.0},
        )

    def test_allows_explicit_vat_amount(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "kind": "sale", "vat_amount": "15.00"},
            {"jurisdiction": "GB", "kind": "purchase", "vat_amount": "3.33"},
        ]
        result = calculate_vat_by_jurisdiction(transactions)
        self.assertEqual(
            result["GB"],
            {"output_vat": 15.0, "input_vat": 3.33, "vat_payable": 11.67},
        )

    def test_rejects_missing_rate_when_needed(self) -> None:
        with self.assertRaisesRegex(ValueError, "no VAT rate"):
            calculate_vat_by_jurisdiction(
                [{"jurisdiction": "IT", "kind": "sale", "amount": "10.00"}]
            )

    def test_parse_rate_flags(self) -> None:
        parsed = parse_rate_flags(["DE=0.19", "FR=0.20"])
        self.assertEqual(str(parsed["DE"]), "0.19")
        self.assertEqual(str(parsed["FR"]), "0.20")


if __name__ == "__main__":
    unittest.main()
