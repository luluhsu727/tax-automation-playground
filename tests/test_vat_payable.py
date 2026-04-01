from decimal import Decimal
import unittest

from vat_payable import (
    format_summary_for_json,
    generate_vat_payable_by_jurisdiction,
)


class VatPayableTests(unittest.TestCase):
    def test_generate_payable_and_refundable_by_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "de", "type": "sale", "net_amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "type": "purchase", "net_amount": "50.00", "vat_rate": "0.19"},
            {"jurisdiction": "fr", "type": "sale", "vat_amount": "20.00"},
            {"jurisdiction": "FR", "type": "purchase", "vat_amount": "40.00"},
        ]

        summary = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            summary["DE"],
            {
                "output_vat": Decimal("19.00"),
                "input_vat": Decimal("9.50"),
                "net_vat": Decimal("9.50"),
                "vat_payable": Decimal("9.50"),
                "vat_refundable": Decimal("0.00"),
            },
        )
        self.assertEqual(
            summary["FR"],
            {
                "output_vat": Decimal("20.00"),
                "input_vat": Decimal("40.00"),
                "net_vat": Decimal("-20.00"),
                "vat_payable": Decimal("0.00"),
                "vat_refundable": Decimal("20.00"),
            },
        )

    def test_format_summary_for_json(self) -> None:
        summary = {
            "US": {
                "output_vat": Decimal("15"),
                "input_vat": Decimal("3.1"),
                "net_vat": Decimal("11.9"),
                "vat_payable": Decimal("11.9"),
                "vat_refundable": Decimal("0"),
            }
        }

        formatted = format_summary_for_json(summary)
        self.assertEqual(
            formatted["US"],
            {
                "output_vat": "15.00",
                "input_vat": "3.10",
                "net_vat": "11.90",
                "vat_payable": "11.90",
                "vat_refundable": "0.00",
            },
        )

    def test_invalid_type_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported transaction type"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "UK", "type": "transfer", "vat_amount": "5"}]
            )


if __name__ == "__main__":
    unittest.main()
