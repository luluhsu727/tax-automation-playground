import unittest
from decimal import Decimal

from vat_payable import (
    Transaction,
    generate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_generates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.19",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount_ex_vat": "50.00",
                "vat_rate": "0.19",
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "amount_ex_vat": "200.00",
                "vat_rate": "0.20",
                "transaction_type": "sale",
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["DE"], Decimal("9.50"))
        self.assertEqual(result["FR"], Decimal("40.00"))

    def test_supports_dataclass_transactions(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="GB",
                amount_ex_vat=Decimal("100.00"),
                vat_rate=Decimal("0.20"),
                transaction_type="sale",
            ),
            Transaction(
                jurisdiction="GB",
                amount_ex_vat=Decimal("40.00"),
                vat_rate=Decimal("0.20"),
                transaction_type="purchase",
            ),
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)
        self.assertEqual(result, {"GB": Decimal("12.00")})

    def test_alias_matches_primary_function(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "amount_ex_vat": "100.00",
                "vat_rate": "0.21",
                "transaction_type": "sale",
            }
        ]
        self.assertEqual(
            generate_vat_payable_by_jurisdiction(transactions),
            generate_vat_to_be_paid_by_jurisdiction(transactions),
        )

    def test_rejects_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "amount_ex_vat": "100.00",
                        "vat_rate": "0.19",
                        "transaction_type": "refund",
                    }
                ]
            )

    def test_rejects_negative_vat_rate(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "amount_ex_vat": "100.00",
                        "vat_rate": "-0.19",
                        "transaction_type": "sale",
                    }
                ]
            )

    def test_rejects_empty_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "   ",
                        "amount_ex_vat": "100.00",
                        "vat_rate": "0.19",
                        "transaction_type": "sale",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
