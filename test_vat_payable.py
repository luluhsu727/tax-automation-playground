import unittest

from vat_payable import compute_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_computes_per_jurisdiction_with_derived_output_vat(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": 1000, "vat_rate": 0.19, "vat_paid": 30},
            {"jurisdiction": "DE", "amount": 500, "vat_rate": 19, "vat_paid": 20},
            {"jurisdiction": "FR", "amount": 200, "vat_rate": 0.20},
        ]

        result = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(
            result,
            {
                "DE": {
                    "output_vat": "285.00",
                    "input_vat": "50.00",
                    "vat_payable": "235.00",
                },
                "FR": {
                    "output_vat": "40.00",
                    "input_vat": "0.00",
                    "vat_payable": "40.00",
                },
            },
        )

    def test_prefers_explicit_vat_collected_when_present(self) -> None:
        transactions = [
            {
                "jurisdiction": "UK",
                "amount": 1000,
                "vat_rate": 0.2,
                "vat_collected": 210,
                "vat_paid": 20,
            }
        ]

        result = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["UK"]["output_vat"], "210.00")
        self.assertEqual(result["UK"]["vat_payable"], "190.00")

    def test_payable_is_clamped_at_zero(self) -> None:
        transactions = [
            {"jurisdiction": "ES", "amount": 100, "vat_rate": 0.1, "vat_paid": 20}
        ]

        result = compute_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["ES"]["vat_payable"], "0.00")

    def test_raises_on_invalid_jurisdiction(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid jurisdiction"):
            compute_vat_payable_by_jurisdiction(
                [{"jurisdiction": "", "amount": 100, "vat_rate": 0.2}]
            )

    def test_raises_on_negative_amount(self) -> None:
        with self.assertRaisesRegex(ValueError, "negative amount"):
            compute_vat_payable_by_jurisdiction(
                [{"jurisdiction": "DE", "amount": -100, "vat_rate": 0.2}]
            )


if __name__ == "__main__":
    unittest.main()
