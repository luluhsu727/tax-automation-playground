import unittest
from decimal import Decimal

from vat import calculate_vat_payable_by_jurisdiction, generate_vat_payable_by_jurisdiction


class VatByJurisdictionTests(unittest.TestCase):
    def test_calculates_net_vat_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "kind": "sale", "vat_amount": "190.00"},
            {"jurisdiction": "DE", "kind": "purchase", "vat_amount": "75.50"},
            {"jurisdiction": "FR", "kind": "output", "amount": "1000", "vat_rate": "0.20"},
            {"jurisdiction": "FR", "kind": "input", "amount": "200", "vat_rate": "0.20"},
            {"jurisdiction": "UK", "kind": "sale", "vat_amount": "25"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("114.50"),
                "FR": Decimal("160.00"),
                "UK": Decimal("25.00"),
            },
        )

    def test_negative_result_means_reclaimable(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "kind": "sale", "vat_amount": "10"},
            {"jurisdiction": "NL", "kind": "purchase", "vat_amount": "20"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["NL"], Decimal("-10.00"))

    def test_alias_function(self) -> None:
        transactions = [{"jurisdiction": "ES", "kind": "sale", "vat_amount": "21"}]
        self.assertEqual(
            generate_vat_payable_by_jurisdiction(transactions),
            {"ES": Decimal("21.00")},
        )

    def test_invalid_kind_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "kind": "refund", "vat_amount": "10"}]
            )

    def test_missing_amount_data_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "kind": "sale", "amount": "100"}]
            )


if __name__ == "__main__":
    unittest.main()
