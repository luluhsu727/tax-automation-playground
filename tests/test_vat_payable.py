from decimal import Decimal
import unittest

from vat_payable import generate_vat_to_be_paid_by_jurisdiction


class TestVATPayableByJurisdiction(unittest.TestCase):
    def test_groups_and_sums_vat_amount_directly(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "vat_amount": "19.99"},
            {"jurisdiction": "DE", "vat_amount": "10.01"},
            {"jurisdiction": "FR", "vat_amount": Decimal("4.50")},
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("30.00"),
                "FR": Decimal("4.50"),
            },
        )

    def test_calculates_from_net_amount_and_rate(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "net_amount": "100", "vat_rate": "0.21"},
            {"jurisdiction": "ES", "net_amount": "50", "vat_rate": "21"},
            {"jurisdiction": "IT", "net_amount": "200", "vat_rate": "22"},
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "ES": Decimal("31.50"),
                "IT": Decimal("44.00"),
            },
        )

    def test_allows_custom_column_names(self) -> None:
        transactions = [
            {"country": "NL", "taxable": "100", "tax_rate": "21"},
            {"country": "NL", "taxable": "100", "tax_rate": "9"},
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(
            transactions,
            jurisdiction_key="country",
            net_amount_key="taxable",
            vat_rate_key="tax_rate",
        )

        self.assertEqual(result, {"NL": Decimal("30.00")})

    def test_raises_on_missing_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid_by_jurisdiction([{"vat_amount": "10"}])

    def test_raises_on_missing_net_or_rate_when_no_vat_amount(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "DE", "net_amount": "100"}]
            )


if __name__ == "__main__":
    unittest.main()
