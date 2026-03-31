import unittest
from decimal import Decimal

from vat_calculator import (
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


class VatCalculatorTests(unittest.TestCase):
    def test_generates_payable_and_credit_per_jurisdiction(self) -> None:
        records = [
            {
                "jurisdiction": "DE",
                "transaction_type": "sale",
                "net_amount": "1000",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "DE",
                "transaction_type": "purchase",
                "net_amount": "200",
                "vat_rate": "19",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "sale",
                "vat_amount": "50",
            },
            {
                "jurisdiction": "FR",
                "transaction_type": "purchase",
                "vat_amount": "80",
            },
        ]

        result = calculate_vat_payable_by_jurisdiction(records)

        self.assertEqual(
            result["DE"],
            {
                "output_vat": Decimal("190.00"),
                "input_vat": Decimal("38.00"),
                "net_vat": Decimal("152.00"),
                "vat_payable": Decimal("152.00"),
                "vat_credit": Decimal("0.00"),
                "status": "payable",
            },
        )
        self.assertEqual(
            result["FR"],
            {
                "output_vat": Decimal("50.00"),
                "input_vat": Decimal("80.00"),
                "net_vat": Decimal("-30.00"),
                "vat_payable": Decimal("0.00"),
                "vat_credit": Decimal("30.00"),
                "status": "credit",
            },
        )

    def test_generate_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        records = [
            {
                "jurisdiction": "UK",
                "transaction_type": "sale",
                "net_amount": "100",
                "vat_rate": "0.2",
            },
            {
                "jurisdiction": "UK",
                "transaction_type": "purchase",
                "vat_amount": "5",
            },
        ]

        result = generate_vat_to_be_paid_for_each_jurisdiction(records)
        self.assertEqual(result, {"UK": Decimal("15.00")})

    def test_validates_required_fields(self) -> None:
        with self.assertRaises(ValueError) as error:
            calculate_vat_payable_by_jurisdiction(
                [{"transaction_type": "sale", "vat_amount": "10"}]
            )
        self.assertIn("jurisdiction", str(error.exception))


if __name__ == "__main__":
    unittest.main()
