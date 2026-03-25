from decimal import Decimal
import unittest

from vat_payable import Transaction, generate_vat_payable_per_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_net_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "net_amount": "100.00",
                "vat_rate": "0.19",
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "net_amount": "50.00",
                "vat_rate": "0.19",
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "net_amount": "120.00",
                "vat_rate": "0.20",
                "transaction_type": "sale",
            },
        ]

        payable = generate_vat_payable_per_jurisdiction(transactions)

        self.assertEqual(
            payable,
            {
                "DE": Decimal("9.50"),
                "FR": Decimal("24.00"),
            },
        )

    def test_supports_explicit_vat_amount(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="NL",
                net_amount=Decimal("200.00"),
                vat_rate=Decimal("0.21"),
                transaction_type="sale",
                vat_amount=Decimal("41.99"),
            )
        ]

        payable = generate_vat_payable_per_jurisdiction(transactions)

        self.assertEqual(payable["NL"], Decimal("41.99"))

    def test_rounds_half_up(self) -> None:
        transactions = [
            {
                "jurisdiction": "SE",
                "net_amount": "10.05",
                "vat_rate": "0.10",
                "transaction_type": "sale",
            }
        ]

        payable = generate_vat_payable_per_jurisdiction(transactions)

        self.assertEqual(payable["SE"], Decimal("1.01"))

    def test_validates_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "transaction_type"):
            generate_vat_payable_per_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "net_amount": "100",
                        "vat_rate": "0.19",
                        "transaction_type": "refund",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
