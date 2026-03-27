from decimal import Decimal
import unittest

from vat_calculator import generate_vat_to_be_paid_by_jurisdiction


class TestVatCalculator(unittest.TestCase):
    def test_generate_vat_to_be_paid_by_jurisdiction_mixed_transactions(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "kind": "sale",
                "taxable_amount": "100.00",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "kind": "purchase",
                "taxable_amount": "40.00",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "FR",
                "kind": "sale",
                "vat_amount": "20.00",
            },
            {
                "jurisdiction": "FR",
                "kind": "purchase",
                "vat_amount": "5.00",
            },
        ]

        result = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("11.40"),  # 19.00 - 7.60
                "FR": Decimal("15.00"),  # 20.00 - 5.00
            },
        )

    def test_invalid_kind_raises_value_error(self) -> None:
        transactions = [{"jurisdiction": "DE", "kind": "refund", "vat_amount": "10.00"}]

        with self.assertRaisesRegex(ValueError, "Unsupported transaction kind"):
            generate_vat_to_be_paid_by_jurisdiction(transactions)

    def test_missing_jurisdiction_raises_value_error(self) -> None:
        transactions = [{"kind": "sale", "vat_amount": "10.00"}]

        with self.assertRaisesRegex(ValueError, "must include a jurisdiction"):
            generate_vat_to_be_paid_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
