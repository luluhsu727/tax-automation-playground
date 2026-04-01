from decimal import Decimal
import json
import subprocess
import sys
import tempfile
import unittest

from vat_payable import build_transaction, calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_payable_for_multiple_jurisdictions(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "kind": "sale", "vat_amount": "190.00"},
            {"jurisdiction": "DE", "kind": "purchase", "vat_amount": "40.00"},
            {"jurisdiction": "FR", "kind": "sale", "vat_amount": "200.00"},
            {"jurisdiction": "FR", "kind": "purchase", "vat_amount": "240.00"},
        ]

        totals = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(totals["DE"], Decimal("150.00"))
        self.assertEqual(totals["FR"], Decimal("-40.00"))

    def test_build_transaction_from_net_and_rate(self) -> None:
        item = build_transaction(
            {
                "jurisdiction": "NL",
                "kind": "sales",
                "net_amount": "100.00",
                "vat_rate": "0.21",
            }
        )
        self.assertEqual(item.vat_amount, Decimal("21.00"))
        self.assertEqual(item.kind, "sale")

    def test_rejects_invalid_kind(self) -> None:
        with self.assertRaises(ValueError):
            build_transaction(
                {"jurisdiction": "ES", "kind": "refund", "vat_amount": "5.00"}
            )

    def test_cli_outputs_json_totals(self) -> None:
        payload = [
            {"jurisdiction": "GB", "kind": "sale", "vat_amount": "50.00"},
            {"jurisdiction": "GB", "kind": "purchase", "vat_amount": "20.00"},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(payload, tmp)
            tmp_path = tmp.name

        proc = subprocess.run(
            [sys.executable, "vat_payable.py", tmp_path],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(proc.stdout)
        self.assertEqual(result, {"GB": "30.00"})


if __name__ == "__main__":
    unittest.main()
