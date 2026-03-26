import tempfile
import unittest
from pathlib import Path

from tax.cli import parse_transactions_from_csv, write_summaries_to_csv
from tax.vat import compute_vat_payable_by_jurisdiction


class CliTests(unittest.TestCase):
    def test_cli_parsing_and_output_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_csv = Path(tmp) / "transactions.csv"
            output_csv = Path(tmp) / "vat.csv"

            input_csv.write_text(
                (
                    "jurisdiction,transaction_type,net_amount,vat_rate\n"
                    "DE,sale,100,0.19\n"
                    "DE,purchase,20,0.19\n"
                    "FR,sale,50,0.20\n"
                ),
                encoding="utf-8",
            )

            tx = parse_transactions_from_csv(input_csv)
            summaries = compute_vat_payable_by_jurisdiction(tx)
            write_summaries_to_csv(output_csv, summaries)

            content = output_csv.read_text(encoding="utf-8")
            self.assertIn("jurisdiction,output_vat,input_vat,vat_payable", content)
            self.assertIn("DE,19.00,3.80,15.20", content)
            self.assertIn("FR,10.00,0.00,10.00", content)


if __name__ == "__main__":
    unittest.main()
