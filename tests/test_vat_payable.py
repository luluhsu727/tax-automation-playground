import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import generate_vat_to_be_paid, load_transactions_from_csv


class VatPayableTests(unittest.TestCase):
    def test_generate_summary_from_explicit_vat_amounts(self) -> None:
        records = [
            {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "120.00"},
            {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "40.00"},
            {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "80.00"},
            {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "90.00"},
        ]

        summary = generate_vat_to_be_paid(records)

        self.assertEqual(summary["DE"]["output_vat"], Decimal("120.00"))
        self.assertEqual(summary["DE"]["input_vat"], Decimal("40.00"))
        self.assertEqual(summary["DE"]["vat_to_be_paid"], Decimal("80.00"))
        self.assertEqual(summary["FR"]["vat_to_be_paid"], Decimal("0.00"))

    def test_generate_summary_from_amount_and_rate(self) -> None:
        records = [
            {"jurisdiction": "ES", "transaction_type": "sale", "amount": "100.00", "vat_rate": "0.21"},
            {"jurisdiction": "ES", "transaction_type": "purchase", "amount": "50.00", "vat_rate": "0.21"},
        ]

        summary = generate_vat_to_be_paid(records)

        self.assertEqual(summary["ES"]["output_vat"], Decimal("21.00"))
        self.assertEqual(summary["ES"]["input_vat"], Decimal("10.50"))
        self.assertEqual(summary["ES"]["vat_to_be_paid"], Decimal("10.50"))

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_to_be_paid(
                [{"jurisdiction": "IT", "transaction_type": "refund", "vat_amount": "20.00"}]
            )

    def test_csv_loads_with_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "transactions.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "jurisdiction,transaction_type,vat_amount",
                        "NL,sale,50.00",
                        "NL,purchase,20.00",
                    ]
                ),
                encoding="utf-8",
            )

            transactions = load_transactions_from_csv(csv_path)
            summary = generate_vat_to_be_paid(transactions)

        self.assertEqual(summary["NL"]["vat_to_be_paid"], Decimal("30.00"))

    def test_json_serializable_output_shape(self) -> None:
        summary = generate_vat_to_be_paid(
            [{"jurisdiction": "BE", "transaction_type": "sale", "vat_amount": "15"}]
        )
        json_output = {
            jurisdiction: {k: str(v) for k, v in totals.items()}
            for jurisdiction, totals in summary.items()
        }
        parsed = json.loads(json.dumps(json_output))
        self.assertEqual(parsed["BE"]["vat_to_be_paid"], "15.00")


if __name__ == "__main__":
    unittest.main()
