from decimal import Decimal
import unittest

from vat_calculator import (
    Transaction,
    VatComputationError,
    calculate_vat_position_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    transaction_from_mapping,
)


class VatCalculatorTests(unittest.TestCase):
    def test_generates_vat_to_be_paid_for_each_jurisdiction(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="DE",
                transaction_type="sale",
                net_amount=Decimal("100.00"),
                vat_rate=Decimal("0.19"),
            ),
            Transaction(
                jurisdiction="DE",
                transaction_type="purchase",
                net_amount=Decimal("20.00"),
                vat_rate=Decimal("0.19"),
            ),
            Transaction(
                jurisdiction="FR",
                transaction_type="sale",
                net_amount=Decimal("120.00"),
                vat_rate=Decimal("0.20"),
            ),
            Transaction(
                jurisdiction="FR",
                transaction_type="purchase",
                net_amount=Decimal("200.00"),
                vat_rate=Decimal("0.20"),
            ),
        ]

        payable = generate_vat_to_be_paid_by_jurisdiction(transactions)

        self.assertEqual(
            payable,
            {
                "DE": Decimal("15.20"),
                "FR": Decimal("0.00"),
            },
        )

    def test_full_position_includes_credit_when_input_exceeds_output(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="NL",
                transaction_type="sale",
                net_amount=Decimal("50.00"),
                vat_rate=Decimal("0.21"),
            ),
            Transaction(
                jurisdiction="NL",
                transaction_type="purchase",
                net_amount=Decimal("100.00"),
                vat_rate=Decimal("0.21"),
            ),
        ]

        position = calculate_vat_position_by_jurisdiction(transactions)
        self.assertEqual(position["NL"]["output_vat"], Decimal("10.50"))
        self.assertEqual(position["NL"]["input_vat"], Decimal("21.00"))
        self.assertEqual(position["NL"]["vat_payable"], Decimal("0.00"))
        self.assertEqual(position["NL"]["vat_credit"], Decimal("10.50"))

    def test_non_taxable_transactions_do_not_contribute_vat(self) -> None:
        transactions = [
            Transaction(
                jurisdiction="ES",
                transaction_type="sale",
                net_amount=Decimal("100.00"),
                vat_rate=Decimal("0.21"),
                taxable=False,
            ),
            Transaction(
                jurisdiction="ES",
                transaction_type="purchase",
                net_amount=Decimal("40.00"),
                vat_rate=Decimal("0.21"),
                taxable=False,
            ),
        ]

        position = calculate_vat_position_by_jurisdiction(transactions)
        self.assertEqual(position["ES"]["output_vat"], Decimal("0.00"))
        self.assertEqual(position["ES"]["input_vat"], Decimal("0.00"))
        self.assertEqual(position["ES"]["vat_payable"], Decimal("0.00"))
        self.assertEqual(position["ES"]["vat_credit"], Decimal("0.00"))

    def test_transaction_from_mapping_requires_fields(self) -> None:
        with self.assertRaises(VatComputationError):
            transaction_from_mapping({"jurisdiction": "DE"})

    def test_unsupported_transaction_type_raises_error(self) -> None:
        invalid = Transaction(
            jurisdiction="DE",
            transaction_type="refund",
            net_amount=Decimal("10.00"),
            vat_rate=Decimal("0.19"),
        )
        with self.assertRaises(VatComputationError):
            calculate_vat_position_by_jurisdiction([invalid])


if __name__ == "__main__":
    unittest.main()
