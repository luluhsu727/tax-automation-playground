from decimal import Decimal
import unittest

from vat_calculator import VATTransaction, generate_vat_payable_by_jurisdiction


class VATCalculatorTests(unittest.TestCase):
    def test_generates_vat_payable_per_jurisdiction(self) -> None:
        transactions = [
            VATTransaction("DE", 1000, 19, "sale"),
            VATTransaction("DE", 200, 19, "purchase"),
            VATTransaction("FR", 500, 0.2, "sale"),
            VATTransaction("FR", 900, 0.2, "purchase"),
            VATTransaction("ES", 50, 21, "sale"),
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result["DE"],
            {
                "output_vat": Decimal("190.00"),
                "input_vat": Decimal("38.00"),
                "net_vat": Decimal("152.00"),
                "vat_payable": Decimal("152.00"),
                "vat_credit": Decimal("0.00"),
            },
        )
        self.assertEqual(
            result["FR"],
            {
                "output_vat": Decimal("100.00"),
                "input_vat": Decimal("180.00"),
                "net_vat": Decimal("-80.00"),
                "vat_payable": Decimal("0.00"),
                "vat_credit": Decimal("80.00"),
            },
        )
        self.assertEqual(
            result["ES"],
            {
                "output_vat": Decimal("10.50"),
                "input_vat": Decimal("0.00"),
                "net_vat": Decimal("10.50"),
                "vat_payable": Decimal("10.50"),
                "vat_credit": Decimal("0.00"),
            },
        )

    def test_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [VATTransaction("", 100, 0.2, "sale")]
            )
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [VATTransaction("DE", -100, 0.2, "sale")]
            )
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [VATTransaction("DE", 100, -1, "sale")]
            )
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [VATTransaction("DE", 100, 0.2, "refund")]  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
