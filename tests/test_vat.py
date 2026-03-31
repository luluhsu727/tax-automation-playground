from decimal import Decimal

import unittest

from vat import (
    calculate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


class VatByJurisdictionTests(unittest.TestCase):
    def test_calculates_vat_payable_grouped_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "19"},
            {"jurisdiction": "DE", "amount": "50.00", "vat_rate": "19"},
            {"jurisdiction": "FR", "amount": "200.00", "vat_rate": "20"},
        ]

        result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": Decimal("28.50"), "FR": Decimal("40.00")})

    def test_handles_decimal_rates_when_explicitly_configured(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "taxable_amount": 75, "rate": Decimal("0.21")},
            {"jurisdiction": "NL", "taxable_amount": 25, "rate": Decimal("0.21")},
        ]

        result = calculate_vat_to_be_paid_by_jurisdiction(
            transactions,
            amount_key="taxable_amount",
            vat_rate_key="rate",
            rates_are_percentages=False,
        )

        self.assertEqual(result, {"NL": Decimal("21.00")})

    def test_negative_amounts_reduce_vat_payable(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "amount": "100", "vat_rate": "20"},
            {"jurisdiction": "GB", "amount": "-10", "vat_rate": "20"},
        ]

        result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(result, {"GB": Decimal("18.00")})

    def test_alias_functions_delegate_to_primary_implementation(self) -> None:
        transactions = [{"jurisdiction": "ES", "amount": "100", "vat_rate": "21"}]

        self.assertEqual(
            generate_vat_to_be_paid_for_each_jurisdiction(transactions),
            {"ES": Decimal("21.00")},
        )
        self.assertEqual(
            generate_vat_to_be_paid_by_jurisdiction(transactions),
            {"ES": Decimal("21.00")},
        )

    def test_raises_for_missing_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required key 'jurisdiction'"):
            calculate_vat_to_be_paid_by_jurisdiction([{"amount": "100", "vat_rate": "20"}])


if __name__ == "__main__":
    unittest.main()
