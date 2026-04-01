import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import (
    generate_vat_to_be_paid,
    generate_vat_to_be_paid_for_each_jurisdiction,
    generate_vat_to_be_paid_from_json,
)


class VatPayableTests(unittest.TestCase):
    def test_generate_vat_to_be_paid_groups_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "vat_amount": "19.00",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "vat_amount": "4.00",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "net_amount": "100.00",
                "vat_rate": "0.20",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "net_amount": "10.00",
                "vat_rate": "0.20",
            },
        ]

        result = generate_vat_to_be_paid(transactions)

        self.assertEqual(["DE", "FR"], list(result.keys()))
        self.assertEqual(Decimal("19.00"), result["DE"].output_vat)
        self.assertEqual(Decimal("4.00"), result["DE"].input_vat)
        self.assertEqual(Decimal("15.00"), result["DE"].vat_to_be_paid)
        self.assertEqual(Decimal("20.00"), result["FR"].output_vat)
        self.assertEqual(Decimal("2.00"), result["FR"].input_vat)
        self.assertEqual(Decimal("18.00"), result["FR"].vat_to_be_paid)

    def test_generate_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "vat_amount": "10.00",
            },
            {
                "jurisdiction": "ES",
                "transaction_type": "purchase",
                "vat_amount": "1.00",
            },
            {
                "jurisdiction": "IT",
                "transaction_type": "sale",
                "vat_amount": "3.20",
            },
        ]

        payable = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
        self.assertEqual({"ES": Decimal("9.00"), "IT": Decimal("3.20")}, payable)

    def test_generate_vat_to_be_paid_allows_refund_position(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "transaction_type": "sale",
                "vat_amount": "7.00",
            },
            {
                "jurisdiction": "ES",
                "transaction_type": "purchase",
                "vat_amount": "12.00",
            },
        ]

        result = generate_vat_to_be_paid(transactions)
        self.assertEqual(Decimal("-5.00"), result["ES"].vat_to_be_paid)

    def test_generate_vat_to_be_paid_validates_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "transaction_type"):
            generate_vat_to_be_paid(
                [
                    {
                        "jurisdiction": "IT",
                        "transaction_type": "refund",
                        "vat_amount": "2.00",
                    }
                ]
            )

    def test_generate_vat_to_be_paid_from_json(self) -> None:
        payload = [
            {
                "jurisdiction": "NL",
                "transaction_type": "sale",
                "net_amount": "50.00",
                "vat_rate": "0.21",
            },
            {
                "jurisdiction": "NL",
                "transaction_type": "purchase",
                "vat_amount": "2.10",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "transactions.json"
            with input_path.open("w", encoding="utf-8") as file_handle:
                json.dump(payload, file_handle)

            result = generate_vat_to_be_paid_from_json(input_path)

        self.assertEqual(Decimal("10.50"), result["NL"].output_vat)
        self.assertEqual(Decimal("2.10"), result["NL"].input_vat)
        self.assertEqual(Decimal("8.40"), result["NL"].vat_to_be_paid)


if __name__ == "__main__":
    unittest.main()
