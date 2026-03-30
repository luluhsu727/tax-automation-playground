import unittest
from decimal import Decimal

from vat_payable import calculate_vat_payable_by_jurisdiction


class CalculateVatPayableByJurisdictionTests(unittest.TestCase):
    def test_calculates_payable_totals_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "output_vat": "120.10", "input_vat": "20.10"},
            {"jurisdiction": "DE", "output_vat": 30, "input_vat": 10},
            {"jurisdiction": "FR", "output_vat": "55.50", "input_vat": "60.00"},
            {"jurisdiction": "IT", "output_vat": "40", "input_vat": "0"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("120.00"),
                "FR": Decimal("-4.50"),
                "IT": Decimal("40.00"),
            },
        )

    def test_supports_custom_key_names(self) -> None:
        transactions = [
            {"country": "ES", "vat_collected": "12.345", "vat_paid": "1.115"},
            {"country": "ES", "vat_collected": "0.005", "vat_paid": "0"},
        ]

        result = calculate_vat_payable_by_jurisdiction(
            transactions,
            jurisdiction_key="country",
            output_vat_key="vat_collected",
            input_vat_key="vat_paid",
        )

        self.assertEqual(result, {"ES": Decimal("11.24")})

    def test_raises_for_missing_required_keys(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "missing required key 'output_vat'"
        ):
            calculate_vat_payable_by_jurisdiction([{"jurisdiction": "NL", "input_vat": 1}])

    def test_raises_for_non_numeric_vat_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid 'output_vat' value 'abc'"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "NL", "output_vat": "abc", "input_vat": 1}]
            )

    def test_raises_for_empty_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "jurisdiction cannot be empty"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": " ", "output_vat": 10, "input_vat": 1}]
            )


if __name__ == "__main__":
    unittest.main()
