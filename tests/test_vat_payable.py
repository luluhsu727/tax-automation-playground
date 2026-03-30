import json
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path

from vat_payable import Transaction, generate_vat_payable_by_jurisdiction, main


class VatPayableTests(unittest.TestCase):
    def test_generates_payable_by_jurisdiction(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("100.00"), Decimal("0.19")),
            Transaction("DE", "purchase", Decimal("50.00"), Decimal("0.19")),
            Transaction("FR", "sale", Decimal("200.00"), Decimal("0.20")),
            Transaction("FR", "purchase", Decimal("10.00"), Decimal("0.20")),
        ]

        report = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(report["DE"]["output_vat"], Decimal("19.00"))
        self.assertEqual(report["DE"]["input_vat"], Decimal("9.50"))
        self.assertEqual(report["DE"]["vat_payable"], Decimal("9.50"))
        self.assertEqual(report["FR"]["output_vat"], Decimal("40.00"))
        self.assertEqual(report["FR"]["input_vat"], Decimal("2.00"))
        self.assertEqual(report["FR"]["vat_payable"], Decimal("38.00"))

    def test_uses_explicit_vat_amount_when_provided(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="NL",
                transaction_type="sale",
                net_amount=Decimal("100.00"),
                vat_rate=Decimal("0.21"),
                vat_amount=Decimal("20.50"),
            ),
        ]

        report = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(report["NL"]["output_vat"], Decimal("20.50"))

    def test_supports_negative_vat_payable(self) -> None:
        transactions = [
            Transaction("ES", "sale", Decimal("50.00"), Decimal("0.21")),
            Transaction("ES", "purchase", Decimal("100.00"), Decimal("0.21")),
        ]

        report = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(report["ES"]["vat_payable"], Decimal("-10.50"))

    def test_from_dict_validates_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            Transaction.from_dict(
                {
                    "jurisdiction": "DE",
                    "transaction_type": "refund",
                    "net_amount": "100.00",
                    "vat_rate": "0.19",
                }
            )

    def test_cli_outputs_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload_path = Path(tmp_dir) / "transactions.json"
            payload_path.write_text(
                json.dumps(
                    [
                        {
                            "jurisdiction": "DE",
                            "transaction_type": "sale",
                            "net_amount": "100.00",
                            "vat_rate": "0.19",
                        },
                        {
                            "jurisdiction": "DE",
                            "transaction_type": "purchase",
                            "net_amount": "20.00",
                            "vat_rate": "0.19",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["vat_payable.py", str(payload_path)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {
                "DE": {
                    "input_vat": "3.80",
                    "output_vat": "19.00",
                    "vat_payable": "15.20",
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
