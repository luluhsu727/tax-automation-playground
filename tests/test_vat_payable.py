import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    Transaction,
    calculate_vat_payable_by_jurisdiction,
    load_transactions,
    transaction_from_record,
)


class TransactionParsingTests(unittest.TestCase):
    def test_parses_vat_amount_directly(self) -> None:
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

    def test_parses_amount_and_percent_rate(self) -> None:
        tx = transaction_from_record(
            {
                "jurisdiction": "FR",
                "type": "output",
                "amount": "100",
                "vat_rate": "20%",
            }
        )
        self.assertEqual(tx.transaction_type, "sale")
        self.assertEqual(tx.vat_amount, Decimal("20.00"))

    def test_rejects_unknown_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            transaction_from_record(
                {
                    "jurisdiction": "NL",
                    "transaction_type": "refund",
                    "vat_amount": "5.00",
                }
            )


class AggregationTests(unittest.TestCase):
    def test_generates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("25.00")),
            Transaction("DE", "purchase", Decimal("10.00")),
            {"jurisdiction": "FR", "type": "sale", "vat_amount": "12.00"},
            {"jurisdiction": "FR", "type": "expense", "vat_amount": "20.00"},
        ]

        actual = calculate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(actual["DE"], Decimal("15.00"))
        self.assertEqual(actual["FR"], Decimal("-8.00"))

    def test_floor_negative_vat_at_zero(self) -> None:
        transactions = [{"jurisdiction": "FR", "type": "purchase", "vat_amount": "20.00"}]
        actual = calculate_vat_payable_by_jurisdiction(transactions, floor_at_zero=True)
        self.assertEqual(actual["FR"], Decimal("0.00"))


class LoadingTests(unittest.TestCase):
    def test_loads_transactions_from_list(self) -> None:
        payload = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "30.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "10.00"},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "transactions.json"
            input_file.write_text(json.dumps(payload), encoding="utf-8")
            transactions = load_transactions(input_file)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].transaction_type, "sale")
        self.assertEqual(transactions[1].transaction_type, "purchase")

    def test_loads_transactions_from_wrapped_object(self) -> None:
        payload = {
            "transactions": [
                {"jurisdiction": "ES", "type": "sale", "vat_amount": 11},
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "transactions.json"
            input_file.write_text(json.dumps(payload), encoding="utf-8")
            transactions = load_transactions(input_file)

        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].jurisdiction, "ES")
        self.assertEqual(transactions[0].vat_amount, Decimal("11.00"))


if __name__ == "__main__":
    unittest.main()
