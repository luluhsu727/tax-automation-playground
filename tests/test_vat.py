from decimal import Decimal
import unittest

from tax.vat import Transaction, compute_vat_payable_by_jurisdiction


class TestVatComputation(unittest.TestCase):
    def test_compute_vat_payable_by_jurisdiction_multiple_regions(self) -> None:
        transactions = [
            Transaction("DE", "sale", Decimal("100.00"), Decimal("0.19")),
            Transaction("DE", "purchase", Decimal("20.00"), Decimal("0.19")),
            Transaction("FR", "sale", Decimal("50.00"), Decimal("0.20")),
            Transaction("FR", "purchase", Decimal("100.00"), Decimal("0.20")),
        ]

        result = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual([row.jurisdiction for row in result], ["DE", "FR"])
        de, fr = result
        self.assertEqual(de.output_vat, Decimal("19.00"))
        self.assertEqual(de.input_vat, Decimal("3.80"))
        self.assertEqual(de.vat_payable, Decimal("15.20"))

        self.assertEqual(fr.output_vat, Decimal("10.00"))
        self.assertEqual(fr.input_vat, Decimal("20.00"))
        self.assertEqual(fr.vat_payable, Decimal("-10.00"))

    def test_rejects_unsupported_transaction_type(self) -> None:
        transactions = [
            Transaction("DE", "refund", Decimal("10.00"), Decimal("0.19")),
        ]

        with self.assertRaisesRegex(ValueError, "Unsupported transaction_type"):
            compute_vat_payable_by_jurisdiction(transactions)


if __name__ == "__main__":
    unittest.main()
