import unittest

from vat_payable import generate_vat_to_be_paid_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_vat_payable_and_refundable_per_jurisdiction(self) -> None:
        transactions = [
            {
                "jurisdiction": "DE",
                "amount": 1000,
                "vat_rate": 0.19,
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "DE",
                "amount": 200,
                "vat_rate": 19,
                "transaction_type": "purchase",
                "deductible": True,
            },
            {
                "jurisdiction": "FR",
                "amount": 100,
                "vat_rate": 20,
                "transaction_type": "sale",
            },
            {
                "jurisdiction": "FR",
                "amount": 250,
                "vat_rate": 0.2,
                "transaction_type": "purchase",
                "deductible": True,
            },
            {
                "jurisdiction": "FR",
                "amount": 30,
                "vat_rate": 20,
                "transaction_type": "purchase",
                "deductible": False,
            },
        ]

        report = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            report["DE"],
            {
                "taxable_sales": 1000.0,
                "taxable_purchases": 200.0,
                "output_vat": 190.0,
                "input_vat_credit": 38.0,
                "net_vat": 152.0,
                "vat_payable": 152.0,
                "vat_refundable": 0.0,
            },
        )
        self.assertEqual(
            report["FR"],
            {
                "taxable_sales": 100.0,
                "taxable_purchases": 280.0,
                "output_vat": 20.0,
                "input_vat_credit": 50.0,
                "net_vat": -30.0,
                "vat_payable": 0.0,
                "vat_refundable": 30.0,
            },
        )

    def test_raises_for_unknown_transaction_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported transaction_type"):
            generate_vat_to_be_paid_by_jurisdiction(
                [
                    {
                        "jurisdiction": "UK",
                        "amount": 100,
                        "vat_rate": 20,
                        "transaction_type": "transfer",
                    }
                ]
            )

    def test_raises_for_missing_required_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required field 'vat_rate'"):
            generate_vat_to_be_paid_by_jurisdiction(
                [{"jurisdiction": "ES", "amount": 100, "transaction_type": "sale"}]
            )


if __name__ == "__main__":
    unittest.main()
