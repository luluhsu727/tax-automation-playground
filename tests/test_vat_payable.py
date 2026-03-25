import unittest
from decimal import Decimal

from vat_payable import calculate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_calculates_vat_to_be_paid_per_jurisdiction(self) -> None:
        rows = [
            {"jurisdiction": "DE", "tax_direction": "sale", "vat_amount": "120.00"},
            {"jurisdiction": "DE", "tax_direction": "purchase", "vat_amount": "20.00"},
            {"jurisdiction": "FR", "tax_direction": "output", "vat_amount": "55.50"},
            {"jurisdiction": "FR", "tax_direction": "input", "vat_amount": "60.50"},
        ]

        summaries = calculate_vat_payable_by_jurisdiction(rows)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0].jurisdiction, "DE")
        self.assertEqual(summaries[0].output_vat, Decimal("120.00"))
        self.assertEqual(summaries[0].input_vat, Decimal("20.00"))
        self.assertEqual(summaries[0].vat_to_be_paid, Decimal("100.00"))
        self.assertEqual(summaries[0].vat_credit, Decimal("0"))

        self.assertEqual(summaries[1].jurisdiction, "FR")
        self.assertEqual(summaries[1].output_vat, Decimal("55.50"))
        self.assertEqual(summaries[1].input_vat, Decimal("60.50"))
        self.assertEqual(summaries[1].vat_to_be_paid, Decimal("0"))
        self.assertEqual(summaries[1].vat_credit, Decimal("5.00"))

    def test_rejects_unsupported_tax_direction(self) -> None:
        rows = [{"jurisdiction": "DE", "tax_direction": "refund", "vat_amount": "10.00"}]
        with self.assertRaisesRegex(ValueError, "Unsupported tax_direction"):
            calculate_vat_payable_by_jurisdiction(rows)

    def test_requires_jurisdiction(self) -> None:
        rows = [{"jurisdiction": " ", "tax_direction": "output", "vat_amount": "10.00"}]
        with self.assertRaisesRegex(ValueError, "missing required field 'jurisdiction'"):
            calculate_vat_payable_by_jurisdiction(rows)


if __name__ == "__main__":
    unittest.main()
