import unittest
from decimal import Decimal

from vat_calculator import calculate_vat_to_be_paid


class TestCalculateVatToBePaid(unittest.TestCase):
    def test_calculates_vat_per_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "transaction_type": "sale", "net_amount": 100, "vat_rate": 0.19},
            {"jurisdiction": "DE", "transaction_type": "purchase", "net_amount": 20, "vat_rate": 0.19},
            {"jurisdiction": "FR", "transaction_type": "sale", "net_amount": 200, "vat_rate": 0.20},
            {"jurisdiction": "FR", "transaction_type": "purchase", "net_amount": 50, "vat_rate": 0.20},
            # Refund-equivalent scenario represented as low sale total, still non-negative.
            {"jurisdiction": "NL", "transaction_type": "sale", "net_amount": 10, "vat_rate": 0.21},
            {"jurisdiction": "NL", "transaction_type": "purchase", "net_amount": 100, "vat_rate": 0.21},
        ]

        actual = calculate_vat_to_be_paid(transactions)

        expected = {
            "DE": {
                "output_vat": Decimal("19.00"),
                "input_vat": Decimal("3.80"),
                "vat_to_be_paid": Decimal("15.20"),
            },
            "FR": {
                "output_vat": Decimal("40.00"),
                "input_vat": Decimal("10.00"),
                "vat_to_be_paid": Decimal("30.00"),
            },
            "NL": {
                "output_vat": Decimal("2.10"),
                "input_vat": Decimal("21.00"),
                "vat_to_be_paid": Decimal("-18.90"),
            },
        }
        self.assertEqual(expected, actual)

    def test_accepts_alias_fields(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "type": "sale", "amount": "100.00", "vat_rate": "0.19"},
            {"jurisdiction": "DE", "type": "purchase", "amount": "20.00", "vat_rate": "0.19"},
        ]
        actual = calculate_vat_to_be_paid(transactions)
        self.assertEqual(Decimal("15.20"), actual["DE"]["vat_to_be_paid"])

    def test_rounds_each_transaction_line(self) -> None:
        transactions = [
            # 0.025 rounds to 0.03 for each line item.
            {"jurisdiction": "DE", "transaction_type": "sale", "net_amount": "0.25", "vat_rate": "0.10"},
            {"jurisdiction": "DE", "transaction_type": "sale", "net_amount": "0.25", "vat_rate": "0.10"},
        ]
        actual = calculate_vat_to_be_paid(transactions)
        self.assertEqual(Decimal("0.06"), actual["DE"]["vat_to_be_paid"])

    def test_rejects_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid(
                [
                    {
                        "jurisdiction": "DE",
                        "transaction_type": "transfer",
                        "net_amount": 100,
                        "vat_rate": 0.19,
                    }
                ]
            )

    def test_rejects_negative_amount(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid(
                [
                    {
                        "jurisdiction": "DE",
                        "transaction_type": "sale",
                        "net_amount": -1,
                        "vat_rate": 0.19,
                    }
                ]
            )

    def test_rejects_invalid_vat_rate(self) -> None:
        with self.assertRaises(ValueError):
            calculate_vat_to_be_paid(
                [
                    {
                        "jurisdiction": "DE",
                        "transaction_type": "sale",
                        "net_amount": 100,
                        "vat_rate": 1.5,
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
