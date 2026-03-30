import unittest
from decimal import Decimal

from vat_calculator import generate_vat_payable_by_jurisdiction


class TestGenerateVatPayableByJurisdiction(unittest.TestCase):
    def test_generates_vat_payable_for_each_jurisdiction(self) -> None:
        transactions = [
            {"jurisdiction": "DE", "amount": "100.00", "transaction_type": "sale"},
            {"jurisdiction": "DE", "amount": "40.00", "transaction_type": "purchase"},
            {"jurisdiction": "FR", "amount": "80.00", "transaction_type": "sale"},
            {"jurisdiction": "FR", "amount": "10.00", "transaction_type": "purchase"},
        ]
        rates = {"DE": "0.19", "FR": "0.20"}

        result = generate_vat_payable_by_jurisdiction(transactions, rates)

        self.assertEqual(
            result["DE"],
            {
                "output_vat": Decimal("19.00"),
                "input_vat": Decimal("7.60"),
                "vat_payable": Decimal("11.40"),
            },
        )
        self.assertEqual(
            result["FR"],
            {
                "output_vat": Decimal("16.00"),
                "input_vat": Decimal("2.00"),
                "vat_payable": Decimal("14.00"),
            },
        )

    def test_uses_transaction_rate_override(self) -> None:
        transactions = [
            {
                "jurisdiction": "ES",
                "amount": "100.00",
                "transaction_type": "sale",
                "vat_rate": "0.10",
            },
            {"jurisdiction": "ES", "amount": "50.00", "transaction_type": "purchase"},
        ]
        rates = {"ES": "0.21"}

        result = generate_vat_payable_by_jurisdiction(transactions, rates)

        self.assertEqual(result["ES"]["output_vat"], Decimal("10.00"))
        self.assertEqual(result["ES"]["input_vat"], Decimal("10.50"))
        self.assertEqual(result["ES"]["vat_payable"], Decimal("-0.50"))

    def test_uses_default_rate_when_jurisdiction_rate_missing(self) -> None:
        transactions = [{"jurisdiction": "NL", "amount": "100", "transaction_type": "sale"}]

        result = generate_vat_payable_by_jurisdiction(
            transactions=transactions,
            jurisdiction_rates={},
            default_rate="0.21",
        )

        self.assertEqual(result["NL"]["vat_payable"], Decimal("21.00"))

    def test_raises_for_missing_rate_without_default(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                transactions=[
                    {"jurisdiction": "NL", "amount": "100", "transaction_type": "sale"}
                ],
                jurisdiction_rates={},
            )

    def test_raises_for_invalid_transaction_type(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                transactions=[
                    {
                        "jurisdiction": "DE",
                        "amount": "100",
                        "transaction_type": "refund",
                    }
                ],
                jurisdiction_rates={"DE": "0.19"},
            )


if __name__ == "__main__":
    unittest.main()
