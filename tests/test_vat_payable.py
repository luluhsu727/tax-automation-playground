from decimal import Decimal
import unittest

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "vat": "120.50"},
            {"jurisdiction": "DE", "type": "purchase", "vat": "20.25"},
            {"jurisdiction": "FR", "type": "sale", "vat": "80"},
            {"jurisdiction": "FR", "type": "purchase", "vat": "90"},
            {"jurisdiction": "DE", "type": "sale", "vat": "10"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("110.25"),
                "FR": Decimal("-10"),
            },
        )

    def test_purchase_only_jurisdiction_is_negative_payable(self) -> None:
        result = calculate_vat_payable_by_jurisdiction(
            [{"jurisdiction": "NL", "type": "purchase", "vat": 12}]
        )
        self.assertEqual(result, {"NL": Decimal("-12")})

    def test_rejects_missing_required_field(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction([{"type": "sale", "vat": 10}])

    def test_rejects_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "type": "refund", "vat": 10}]
            )


if __name__ == "__main__":
    unittest.main()
