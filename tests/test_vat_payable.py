from decimal import Decimal
import unittest

from vat_automation import (
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
    summarize_vat_by_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_generate_vat_payable_for_each_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "type": "sale", "amount": "1000", "vat_rate": "0.20"},
            {"jurisdiction": "FR", "type": "purchase", "amount": "200", "vat_rate": "0.20"},
            {"jurisdiction": "DE", "type": "sale", "vat_amount": "190"},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": "40"},
            {"jurisdiction": "DE", "type": "purchase", "vat_amount": "20"},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("130.00"),
                "FR": Decimal("160.00"),
            },
        )

    def test_clamp_negative_payable_to_zero(self) -> None:
        transactions = [
            {"jurisdiction": "NL", "type": "sale", "vat_amount": "10"},
            {"jurisdiction": "NL", "type": "purchase", "vat_amount": "25"},
        ]

        result = calculate_vat_payable_by_jurisdiction(
            transactions, clamp_negative_payable=True
        )

        self.assertEqual(result["NL"], Decimal("0.00"))

    def test_summary_contains_output_and_input_components(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "type": "sale", "vat_amount": "120"},
            {"jurisdiction": "ES", "type": "purchase", "vat_amount": "75"},
        ]

        summary = summarize_vat_by_jurisdiction(transactions)

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0].jurisdiction, "ES")
        self.assertEqual(summary[0].output_vat, Decimal("120.00"))
        self.assertEqual(summary[0].input_vat, Decimal("75.00"))
        self.assertEqual(summary[0].vat_payable, Decimal("45.00"))

    def test_raises_on_unknown_transaction_type(self) -> None:
        transactions = [{"jurisdiction": "IT", "type": "refund", "vat_amount": "10"}]

        with self.assertRaisesRegex(ValueError, "Unsupported transaction type"):
            generate_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()

