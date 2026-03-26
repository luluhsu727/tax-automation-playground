import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    Transaction,
    VATSummary,
    calculate_transaction_vat,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    load_transactions,
    transaction_from_record,
)


class TransactionParsingTests(unittest.TestCase):
    def test_transaction_from_vat_amount(self) -> None:
        tx = transaction_from_record(
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": "12.345",
            }
        )
        self.assertEqual(tx.jurisdiction, "DE")
        self.assertEqual(tx.transaction_type, "sale")
        self.assertEqual(tx.vat_amount, Decimal("12.35"))

    def test_transaction_from_net_and_rate_percent(self) -> None:
        tx = transaction_from_record(
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "net_amount": "100",
                "vat_rate": 20,
            }
        )
        self.assertEqual(tx.vat_amount, Decimal("20.00"))

    def test_transaction_requires_valid_type(self) -> None:
        with self.assertRaises(ValueError):
            transaction_from_record(
                {
                    "jurisdiction": "US",
                    "transaction_type": "refund",
                    "vat_amount": 1,
                }
            )


class VatAggregationTests(unittest.TestCase):
    def test_calculate_vat_payable_by_jurisdiction(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("25.00")),
            Transaction("DE", "purchase", Decimal("10.00")),
            Transaction("FR", "sale", Decimal("12.00")),
            Transaction("FR", "purchase", Decimal("20.00")),
        ]

        actual = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(actual["DE"], Decimal("15.00"))
        self.assertEqual(actual["FR"], Decimal("-8.00"))

    def test_floor_negative_vat_at_zero(self) -> None:
        transactions = [Transaction("FR", "purchase", Decimal("20.00"))]
        actual = calculate_vat_payable_by_jurisdiction(transactions, floor_at_zero=True)
        self.assertEqual(actual["FR"], Decimal("0.00"))


class GeneratorCompatibilityTests(unittest.TestCase):
    def test_generate_vat_to_be_paid_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "vat_amount": "19.99"},
            {"jurisdiction": "DE", "vat_amount": "10.01"},
            {"jurisdiction": "FR", "vat_amount": Decimal("4.50")},
        ]
        result = generate_vat_to_be_paid_by_jurisdiction(transactions)
        self.assertEqual(result, {"DE": Decimal("30.00"), "FR": Decimal("4.50")})

    def test_generate_vat_payable_structured_summary(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "taxable_amount": 100,
                "vat_rate": 0.19,
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "taxable_amount": 20,
                "vat_rate": 0.19,
            },
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "0.81"},
        ]
        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertIsInstance(result["DE"], VATSummary)
        self.assertEqual(result["DE"].output_vat, Decimal("19.81"))
        self.assertEqual(result["DE"].input_vat, Decimal("3.80"))
        self.assertEqual(result["DE"].vat_payable, Decimal("16.01"))

    def test_generate_vat_payable_supports_list_comparison(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "transaction_type": "output", "vat_amount": "40.00"},
            {"jurisdiction": "FR", "transaction_type": "input", "vat_amount": "55.00"},
        ]
        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(
            result,
            [
                {
                    "jurisdiction": "FR",
                    "output_vat": Decimal("40.00"),
                    "input_vat": Decimal("55.00"),
                    "net_vat": Decimal("-15.00"),
                    "vat_payable": Decimal("0.00"),
                    "vat_refundable": Decimal("15.00"),
                }
            ],
        )
        self.assertEqual(result[0]["jurisdiction"], "FR")

    def test_calculate_transaction_vat(self) -> None:
        self.assertEqual(calculate_transaction_vat({"vat_amount": "12.345"}), Decimal("12.35"))
        self.assertEqual(
            calculate_transaction_vat({"taxable_amount": "100.00", "vat_rate": "20"}),
            Decimal("20.00"),
        )


class LoadTransactionsTests(unittest.TestCase):
    def test_load_transactions(self) -> None:
        payload = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "30.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "10.00"},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "tx.json"
            file_path.write_text(json.dumps(payload), encoding="utf-8")
            transactions = load_transactions(file_path)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].jurisdiction, "DE")
        self.assertEqual(transactions[1].transaction_type, "purchase")


if __name__ == "__main__":
    unittest.main()
