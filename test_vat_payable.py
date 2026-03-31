import tempfile
import textwrap
import unittest
from decimal import Decimal
from pathlib import Path

from vat_payable import aggregate_vat_payable, load_transactions_from_csv


class VatPayableTests(unittest.TestCase):
    def _write_temp_csv(self, content: str) -> Path:
        temp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv")
        temp.write(textwrap.dedent(content).strip() + "\n")
        temp.close()
        return Path(temp.name)

    def test_aggregates_vat_payable_by_jurisdiction(self) -> None:
        csv_path = self._write_temp_csv(
            """
            jurisdiction,transaction_type,vat_amount
            DE,sale,50.00
            DE,purchase,10.00
            FR,sale,20.00
            FR,purchase,25.50
            """
        )

        transactions = load_transactions_from_csv(csv_path)
        totals = aggregate_vat_payable(transactions)

        self.assertEqual(
            totals,
            {
                "DE": Decimal("40.00"),
                "FR": Decimal("-5.50"),
            },
        )

    def test_calculates_vat_amount_from_net_and_rate_when_missing(self) -> None:
        csv_path = self._write_temp_csv(
            """
            jurisdiction,transaction_type,net_amount,vat_rate
            ES,sale,100.00,0.21
            ES,purchase,30.00,0.21
            """
        )

        transactions = load_transactions_from_csv(csv_path)
        totals = aggregate_vat_payable(transactions)

        self.assertEqual(totals, {"ES": Decimal("14.70")})

    def test_errors_on_unknown_transaction_type(self) -> None:
        csv_path = self._write_temp_csv(
            """
            jurisdiction,transaction_type,vat_amount
            GB,refund,12.50
            """
        )

        with self.assertRaisesRegex(ValueError, "Invalid transaction_type"):
            load_transactions_from_csv(csv_path)


if __name__ == "__main__":
    unittest.main()
