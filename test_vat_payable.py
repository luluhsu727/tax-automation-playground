import unittest

from vat_payable import (
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_per_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_groups_and_nets_by_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount": 100,
                "vat_rate": 0.19,
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount": 50,
                "vat_rate": 0.19,
                "transaction_type": "purchase",
            },
            {
                "jurisdiction": "FR",
                "amount": 200,
                "vat_rate": 20,
                "transaction_type": "sale",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"DE": 9.5, "FR": 40.0})

    def test_uses_explicit_vat_amount_when_provided(self) -> None:
        transactions = [
            {"jurisdiction": "GB", "vat_amount": 17.55, "transaction_type": "sale"},
            {"jurisdiction": "GB", "vat_amount": 2.55, "transaction_type": "purchase"},
        ]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"GB": 15.0})

    def test_defaults_transaction_type_to_sale(self) -> None:
        transactions = [{"jurisdiction": "ES", "amount": 100, "vat_rate": 0.21}]

        result = calculate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result, {"ES": 21.0})

    def test_alternate_name_generates_same_result(self) -> None:
        transactions = [{"jurisdiction": "IT", "amount": 100, "vat_rate": 0.22}]

        result = generate_vat_to_be_paid_per_jurisdiction(transactions)

        self.assertEqual(result, {"IT": 22.0})

    def test_raises_for_missing_required_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing jurisdiction"):
            calculate_vat_payable_by_jurisdiction([{"amount": 100, "vat_rate": 0.2}])

        with self.assertRaisesRegex(ValueError, "missing amount"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "vat_rate": 0.2}]
            )

        with self.assertRaisesRegex(ValueError, "missing vat_rate"):
            calculate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "amount": 100}]
            )

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid transaction_type"):
            calculate_vat_payable_by_jurisdiction(
                [
                    {
                        "jurisdiction": "DE",
                        "amount": 100,
                        "vat_rate": 0.2,
                        "transaction_type": "refund",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
