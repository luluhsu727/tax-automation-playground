import unittest
from decimal import Decimal

from vat import VATEntry, generate_vat_payable_by_jurisdiction


class TestVATGeneration(unittest.TestCase):
    def test_generate_vat_payable_for_multiple_jurisdictions(self) -> None:
        entries = [
            VATEntry(jurisdiction="DE", output_vat="100.00", input_vat="40.00"),
            VATEntry(jurisdiction="DE", output_vat="50.00", input_vat="30.00"),
            VATEntry(jurisdiction="FR", output_vat="20.00", input_vat="25.00"),
            VATEntry(jurisdiction="FR", output_vat="10.00", input_vat="2.00"),
        ]

        result = generate_vat_payable_by_jurisdiction(entries)

        self.assertEqual(result["DE"].total_output_vat, Decimal("150.00"))
        self.assertEqual(result["DE"].total_input_vat, Decimal("70.00"))
        self.assertEqual(result["DE"].net_vat, Decimal("80.00"))
        self.assertEqual(result["DE"].vat_payable, Decimal("80.00"))
        self.assertEqual(result["DE"].vat_credit_carry_forward, Decimal("0.00"))

        self.assertEqual(result["FR"].total_output_vat, Decimal("30.00"))
        self.assertEqual(result["FR"].total_input_vat, Decimal("27.00"))
        self.assertEqual(result["FR"].net_vat, Decimal("3.00"))
        self.assertEqual(result["FR"].vat_payable, Decimal("3.00"))
        self.assertEqual(result["FR"].vat_credit_carry_forward, Decimal("0.00"))

    def test_generate_vat_credit_when_input_exceeds_output(self) -> None:
        entries = [
            VATEntry(jurisdiction="ES", output_vat="11.10", input_vat="20.00"),
        ]

        result = generate_vat_payable_by_jurisdiction(entries)

        self.assertEqual(result["ES"].net_vat, Decimal("-8.90"))
        self.assertEqual(result["ES"].vat_payable, Decimal("0.00"))
        self.assertEqual(result["ES"].vat_credit_carry_forward, Decimal("8.90"))

    def test_rounding_uses_half_up_to_two_decimals(self) -> None:
        entries = [
            VATEntry(jurisdiction="NL", output_vat="10.005", input_vat="0"),
        ]

        result = generate_vat_payable_by_jurisdiction(entries)

        self.assertEqual(result["NL"].total_output_vat, Decimal("10.01"))
        self.assertEqual(result["NL"].vat_payable, Decimal("10.01"))
