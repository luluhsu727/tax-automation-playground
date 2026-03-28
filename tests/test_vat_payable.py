import unittest
from decimal import Decimal

from vat_payable import (
    Transaction,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    transaction_from_record,
)


class TransactionParsingTests(unittest.TestCase):
    def test_parses_vat_amount_directly(self) -> None:
        tx = transaction_from_record(
            {
                "jurisdiction": "de",
                "transaction_type": "sale",
                "vat_amount": "12.345",
            }
        )

        self.assertEqual(tx.jurisdiction, "DE")
        self.assertEqual(tx.transaction_type, "sale")
        self.assertEqual(tx.vat_amount, Decimal("12.35"))

    def test_parses_amount_and_percent_rate(self) -> None:
        tx = transaction_from_record(
            {
                "country": "fr",
                "type": "purchase",
                "amount": "100",
                "vat_rate": 20,
            }
        )

        self.assertEqual(tx.jurisdiction, "FR")
        self.assertEqual(tx.transaction_type, "purchase")
        self.assertEqual(tx.vat_amount, Decimal("20.00"))

    def test_raises_for_missing_required_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "jurisdiction/country"):
            transaction_from_record({"transaction_type": "sale", "vat_amount": "1.00"})

        with self.assertRaisesRegex(ValueError, "amount/net_amount"):
            transaction_from_record({"jurisdiction": "DE", "vat_rate": "0.19"})

        with self.assertRaisesRegex(ValueError, "vat_rate"):
            transaction_from_record({"jurisdiction": "DE", "amount": "10"})

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported transaction_type"):
            transaction_from_record(
                {
                    "jurisdiction": "DE",
                    "transaction_type": "refund",
                    "vat_amount": "1.00",
                }
            )


class VatPayableAggregationTests(unittest.TestCase):
    def test_generates_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("19.00")),
            Transaction("DE", "purchase", Decimal("9.50")),
            Transaction("FR", "sale", Decimal("40.00")),
            Transaction("FR", "purchase", Decimal("10.00")),
            {"jurisdiction": "ES", "amount": 100, "vat_rate": 0.21, "transaction_type": "sale"},
        ]

        result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("9.50"),
                "ES": Decimal("21.00"),
                "FR": Decimal("30.00"),
            },
        )

    def test_can_floor_negative_totals_to_zero(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "12.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions, floor_at_zero=True)
        self.assertEqual(result, {"FR": Decimal("0.00")})

    def test_float_api_wrapper_returns_floats(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "transaction_type": "sale", "vat_amount": "17.55"},
            {"jurisdiction": "GB", "transaction_type": "purchase", "vat_amount": "2.55"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"GB": 15.0})
        self.assertIsInstance(result["GB"], float)


if __name__ == "__main__":
    unittest.main()
