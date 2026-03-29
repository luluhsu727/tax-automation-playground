import unittest

from vat_payable import generate_vat_payable_by_jurisdiction


class VatPayableTests(unittest.TestCase):
    def test_generates_payable_and_credit_per_jurisdiction(self) -> None:
        transactions = [
            # UK: net payable (output VAT > recoverable input VAT)
            {"jurisdiction": "UK", "type": "sale", "amount": 1000, "vat_rate": 0.2},
            {"jurisdiction": "UK", "type": "purchase", "amount": 200, "vat_rate": 20},
            # DE: net credit (recoverable input VAT > output VAT)
            {"jurisdiction": "DE", "type": "sale", "amount": 100, "vat_rate": 19},
            {"jurisdiction": "DE", "type": "purchase", "amount": 300, "vat_rate": 0.19},
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["UK"]["output_vat"], 200)
        self.assertEqual(result["UK"]["input_vat_recoverable"], 40)
        self.assertEqual(result["UK"]["net_vat"], 160)
        self.assertEqual(result["UK"]["vat_payable"], 160)
        self.assertEqual(result["UK"]["vat_credit"], 0)

        self.assertEqual(result["DE"]["output_vat"], 19)
        self.assertEqual(result["DE"]["input_vat_recoverable"], 57)
        self.assertEqual(result["DE"]["net_vat"], -38)
        self.assertEqual(result["DE"]["vat_payable"], 0)
        self.assertEqual(result["DE"]["vat_credit"], 38)

    def test_non_recoverable_input_vat_is_excluded(self) -> None:
        transactions = [
            {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.2},
            {
                "jurisdiction": "FR",
                "type": "purchase",
                "amount": 100,
                "vat_rate": 0.2,
                "input_vat_recoverable": False,
            },
        ]

        result = generate_vat_payable_by_jurisdiction(transactions)

        self.assertEqual(result["FR"]["output_vat"], 100)
        self.assertEqual(result["FR"]["input_vat_recoverable"], 0)
        self.assertEqual(result["FR"]["vat_payable"], 100)

    def test_raises_on_invalid_payload(self) -> None:
        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "UK", "type": "other", "amount": 1, "vat_rate": 0.2}]
            )

        with self.assertRaises(ValueError):
            generate_vat_payable_by_jurisdiction(
                [{"jurisdiction": "", "type": "sale", "amount": 1, "vat_rate": 0.2}]
            )


if __name__ == "__main__":
    unittest.main()
