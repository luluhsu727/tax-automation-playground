import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.vat_payable import vat_payable_by_jurisdiction


class VatPayableByJurisdictionTests(unittest.TestCase):
    def test_aggregates_multiple_records_per_jurisdiction(self) -> None:
        records = [
            {"jurisdiction": "DE", "output_vat": 120.0, "input_vat": 20.0},
            {"jurisdiction": "DE", "output_vat": 30.0, "input_vat": 10.0},
            {"jurisdiction": "FR", "output_vat": 50.0, "input_vat": 5.0},
        ]

        result = vat_payable_by_jurisdiction(records)
        self.assertEqual(result, {"DE": 120.0, "FR": 45.0})

    def test_derives_vat_from_amounts_and_rates(self) -> None:
        records = [
            {
                "jurisdiction": "ES",
                "sales_amount": 1000,
                "vat_rate": 0.21,
                "purchase_amount": 200,
                "deductible_vat_rate": 0.21,
            },
            {
                "jurisdiction": "IT",
                "sales_amount": 1000,
                "vat_rate": 22,
                "purchase_amount": 100,
                "deductible_vat_rate": 22,
            },
        ]

        result = vat_payable_by_jurisdiction(records)
        self.assertEqual(result, {"ES": 168.0, "IT": 198.0})

    def test_negative_payable_is_clamped_to_zero(self) -> None:
        records = [
            {"jurisdiction": "NL", "output_vat": 50, "input_vat": 80},
        ]

        result = vat_payable_by_jurisdiction(records)
        self.assertEqual(result, {"NL": 0.0})

    def test_rounds_to_two_decimals(self) -> None:
        records = [
            {
                "jurisdiction": "BE",
                "sales_amount": 10.015,
                "vat_rate": 0.2,
                "purchase_amount": 0,
                "deductible_vat_rate": 0.2,
            }
        ]

        result = vat_payable_by_jurisdiction(records)
        self.assertEqual(result, {"BE": 2.0})

    def test_requires_valid_jurisdiction(self) -> None:
        with self.assertRaises(ValueError):
            vat_payable_by_jurisdiction([{"output_vat": 10, "input_vat": 1}])


class VatPayableCliTests(unittest.TestCase):
    def test_cli_prints_json_result(self) -> None:
        payload = [
            {"jurisdiction": "DE", "output_vat": 25, "input_vat": 5},
            {"jurisdiction": "FR", "output_vat": 30, "input_vat": 9},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "records.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                ["python3", "-m", "src.vat_payable", str(input_path)],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(json.loads(completed.stdout), {"DE": 20.0, "FR": 21.0})


if __name__ == "__main__":
    unittest.main()
