from decimal import Decimal
import unittest

from vat_payable import build_cli_output, generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generate_vat_payable_by_jurisdiction_with_mixed_transactions(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "net_amount": "1000", "vat_rate": "0.19", "transaction_type": "sale"},
            {"jurisdiction": "DE", "net_amount": "200", "vat_rate": "0.19", "transaction_type": "refund"},
            {"jurisdiction": "FR", "net_amount": "500", "vat_rate": "0.20", "transaction_type": "sale"},
            {"jurisdiction": "FR", "vat_amount": "25.00", "transaction_type": "purchase_refund"},
            {"jurisdiction": "FR", "vat_amount": "10.00", "transaction_type": "purchase"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("152.00"),
                "FR": Decimal("115.00"),
            },
        )

    def test_generate_uses_default_vat_rate_when_transaction_rate_missing(self) -> None:
        transactions = [{"jurisdiction": "ES", "net_amount": "100.00"}]

        result = generate_vat_payable_by_jurisdiction(
            transactions=transactions,
            default_vat_rates={"ES": "0.21"},
        )

        self.assertEqual(result, {"ES": Decimal("21.00")})

    def test_build_cli_output_stringifies_monetary_values(self) -> None:
        payload = {
            "default_vat_rates": {"NL": "0.21"},
            "transactions": [
                {"jurisdiction": "NL", "net_amount": "120.00"},
                {"jurisdiction": "NL", "vat_amount": "4.80", "transaction_type": "refund"},
            ],
        }

        result = build_cli_output(payload)

        self.assertEqual(
            result,
            {
                "vat_payable_by_jurisdiction": {"NL": "20.40"},
                "total_vat_payable": "20.40",
            },
        )

    def test_invalid_transaction_type_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid 'transaction_type'"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "vat_amount": "3", "transaction_type": "unknown"}]
            )

    def test_missing_jurisdiction_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing 'jurisdiction'"):
            generate_vat_payable_by_jurisdiction([{"vat_amount": "3"}])


if __name__ == "__main__":
    unittest.main()
