from decimal import Decimal
import unittest

from tax_automation import Transaction, generate_vat_payable_by_jurisdiction


class VatGenerationTests(unittest.TestCase):
    def test_generates_vat_payable_and_credit_per_jurisdiction(self) -> None:
        transactions = [
            # France: output > input => payable
            Transaction(
                jurisdiction="FR",
                net_amount=Decimal("1000"),
                vat_rate=Decimal("0.20"),
                transaction_type="sale",
            ),
            Transaction(
                jurisdiction="FR",
                net_amount=Decimal("200"),
                vat_rate=Decimal("0.20"),
                transaction_type="purchase",
            ),
            # Germany: input > output => credit
            Transaction(
                jurisdiction="DE",
                net_amount=Decimal("100"),
                vat_rate=Decimal("0.19"),
                transaction_type="sale",
            ),
            Transaction(
                jurisdiction="DE",
                net_amount=Decimal("1000"),
                vat_rate=Decimal("0.19"),
                transaction_type="purchase",
            ),
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["FR"].output_vat, Decimal("200.00"))
        self.assertEqual(result["FR"].input_vat, Decimal("40.00"))
        self.assertEqual(result["FR"].net_vat, Decimal("160.00"))
        self.assertEqual(result["FR"].vat_payable, Decimal("160.00"))
        self.assertEqual(result["FR"].vat_credit, Decimal("0.00"))

        self.assertEqual(result["DE"].output_vat, Decimal("19.00"))
        self.assertEqual(result["DE"].input_vat, Decimal("190.00"))
        self.assertEqual(result["DE"].net_vat, Decimal("-171.00"))
        self.assertEqual(result["DE"].vat_payable, Decimal("0.00"))
        self.assertEqual(result["DE"].vat_credit, Decimal("171.00"))

    def test_accepts_mapping_payloads(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "net_amount": "100.00",
                "vat_rate": "0.21",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "ES",
                "net_amount": "10.00",
                "vat_rate": "0.21",
                "transaction_type": "purchase",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["ES"].vat_payable, Decimal("18.90"))
        self.assertEqual(result["ES"].vat_credit, Decimal("0.00"))

    def test_rounds_half_up(self) -> None:
        transactions = [
            {
                "jurisdiction": "GB",
                "net_amount": "0.05",
                "vat_rate": "0.10",  # VAT = 0.005 => 0.01
                "transaction_type": "sale",
            }
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["GB"].output_vat, Decimal("0.01"))
        self.assertEqual(result["GB"].vat_payable, Decimal("0.01"))

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "IT",
                        "net_amount": "100",
                        "vat_rate": "0.22",
                        "transaction_type": "refund",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
