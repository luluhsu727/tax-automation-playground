import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    Transaction,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
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
                "kind": "output",
                "net_amount": "100",
                "vat_rate": "20%",
            }
        )
        self.assertEqual(tx.vat_amount, Decimal("20.00"))
        self.assertEqual(tx.transaction_type, "sale")

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

    def test_generate_vat_payable_breakdown(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sales", "vat_amount": "40"},
            {"jurisdiction": "DE", "type": "input", "vat_amount": "10"},
            {"jurisdiction": "FR", "type": "purchase", "vat_amount": "8"},
        ]

        summary = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(summary["DE"]["output_vat"], Decimal("40.00"))
        self.assertEqual(summary["DE"]["input_vat"], Decimal("10.00"))
        self.assertEqual(summary["DE"]["net_vat"], Decimal("30.00"))
        self.assertEqual(summary["DE"]["vat_to_be_paid"], Decimal("30.00"))
        self.assertEqual(summary["DE"]["vat_credit"], Decimal("0.00"))
        self.assertEqual(summary["FR"]["net_vat"], Decimal("-8.00"))
        self.assertEqual(summary["FR"]["vat_to_be_paid"], Decimal("0.00"))
        self.assertEqual(summary["FR"]["vat_credit"], Decimal("8.00"))

    def test_floor_negative_vat_at_zero(self) -> None:
        transactions = [Transaction("FR", "purchase", Decimal("20.00"))]
        actual = calculate_vat_payable_by_jurisdiction(transactions, floor_at_zero=True)
        self.assertEqual(actual["FR"], Decimal("0.00"))

        summary = generate_vat_payable_by_jurisdiction(transactions, floor_at_zero=True)
        self.assertEqual(summary["FR"]["net_vat"], Decimal("0.00"))
        self.assertEqual(summary["FR"]["vat_to_be_paid"], Decimal("0.00"))
        self.assertEqual(summary["FR"]["vat_credit"], Decimal("0.00"))


class LoadTransactionsTests(unittest.TestCase):
    def test_load_transactions_json(self) -> None:
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

    def test_load_transactions_csv(self) -> None:
        rows = [
            {
                "jurisdiction": "DE",
                "kind": "sale",
                "net_amount": "100",
                "vat_rate": "0.19",
            },
            {
                "jurisdiction": "DE",
                "kind": "purchase",
                "vat_amount": "5.00",
                "net_amount": "",
                "vat_rate": "",
            },
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "tx.csv"
            with file_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["jurisdiction", "kind", "net_amount", "vat_rate", "vat_amount"],
                )
                writer.writeheader()
                writer.writerows(rows)
            transactions = load_transactions(file_path)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].vat_amount, Decimal("19.00"))
        self.assertEqual(transactions[1].vat_amount, Decimal("5.00"))


if __name__ == "__main__":
    unittest.main()
