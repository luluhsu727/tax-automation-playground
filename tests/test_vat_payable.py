import unittest

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_aggregates_vat_by_jurisdiction(self) -> None:
        records = [
            {"jurisdiction": "DE", "output_vat": "100.00", "input_vat": "20.00"},
            {"jurisdiction": "DE", "output_vat": "10.25", "input_vat": "2.15"},
            {"jurisdiction": "FR", "output_vat": "50.00", "input_vat": "70.00"},
        ]

        result = generate_vat_payable_by_jurisdiction(records)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": "110.25",
                    "input_vat": "22.15",
                    "vat_payable": "88.10",
                },
                "FR": {
                    "output_vat": "50.00",
                    "input_vat": "70.00",
                    "vat_payable": "-20.00",
                },
            },
        )

    def test_rejects_missing_required_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing 'jurisdiction'"):
            generate_vat_payable_by_jurisdiction(
                [{"output_vat": 1, "input_vat": 1}]
            )

        with self.assertRaisesRegex(ValueError, "missing 'output_vat'"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "input_vat": 1}]
            )

        with self.assertRaisesRegex(ValueError, "missing 'input_vat'"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "output_vat": 1}]
            )

    def test_rejects_invalid_numeric_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid numeric value"):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "output_vat": "NaN?", "input_vat": 1}]
            )


if __name__ == "__main__":
    unittest.main()
