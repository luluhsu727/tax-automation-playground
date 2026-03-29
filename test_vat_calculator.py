import unittest

from vat_calculator import generate_vat_payable_by_jurisdiction


class VatCalculatorTests(unittest.TestCase):
    def test_generates_payable_vat_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": 100, "vat_rate": 19, "kind": "sale"},
            {"jurisdiction": "DE", "amount": 50, "vat_rate": 19, "kind": "purchase"},
            {"jurisdiction": "FR", "amount": 80, "vat_rate": 0.20, "kind": "sale"},
            {
                "jurisdiction": "FR",
                "amount": 40,
                "vat_rate": 20,
                "kind": "purchase",
                "is_vat_deductible": False,
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        # DE: 100*0.19 - 50*0.19 = 9.50
        # FR: 80*0.20 - 0 (non-deductible purchase) = 16.00
        self.assertEqual(result, {"DE": 9.5, "FR": 16.0})

    def test_invalid_kind_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "ES", "amount": 100, "vat_rate": 21, "kind": "refund"}]
            )

    def test_missing_jurisdiction_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction([{"amount": 100, "vat_rate": 21}])


if __name__ == "__main__":
    unittest.main()
