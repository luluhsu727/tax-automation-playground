import unittest
from decimal import Decimal

from vat import Transaction, generate_vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_generates_net_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            Transaction.build("DE", "sale", "1000.00", "0.19"),     # +190.00
            Transaction.build("DE", "purchase", "200.00", "0.19"),  # -38.00
            Transaction.build("FR", "sale", "500.00", "0.20"),      # +100.00
            Transaction.build("FR", "purchase", "700.00", "0.20"),  # -140.00
            Transaction.build("ES", "sale", "100.00", "0.21"),      # +21.00
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": Decimal("152.00"),
                "ES": Decimal("21.00"),
                "FR": Decimal("-40.00"),
            },
        )

    def test_rounds_each_transaction_vat_half_up(self) -> None:
        transactions = [
            Transaction.build("IT", "sale", "1.00", "0.335"),       # +0.34
            Transaction.build("IT", "purchase", "1.00", "0.125"),   # -0.13
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result["IT"], Decimal("0.21"))

    def test_raises_for_unsupported_transaction_type(self) -> None:
        bad = Transaction.build("NL", "sale", "10.00", "0.21")
        # Dataclass is frozen, so replace with a malformed object to emulate invalid upstream input.
        malformed = object.__new__(Transaction)
        object.__setattr__(malformed, "jurisdiction", bad.jurisdiction)
        object.__setattr__(malformed, "transaction_type", "refund")
        object.__setattr__(malformed, "net_amount", bad.net_amount)
        object.__setattr__(malformed, "vat_rate", bad.vat_rate)

        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction([malformed])


if __name__ == "__main__":
    unittest.main()
