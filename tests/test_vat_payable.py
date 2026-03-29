import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from vat_payable import Transaction, calculate_vat_payable_by_jurisdiction, read_transactions_from_csv


def test_calculate_vat_payable_by_jurisdiction():
    transactions = [
        Transaction("DE", "sale", Decimal("100.00"), Decimal("0.19")),
        Transaction("DE", "purchase", Decimal("20.00"), Decimal("0.19")),
        Transaction("FR", "sale", Decimal("200.00"), Decimal("0.20")),
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"]["output_vat"] == Decimal("19.00")
    assert result["DE"]["input_vat"] == Decimal("3.80")
    assert result["DE"]["vat_to_be_paid"] == Decimal("15.20")

    assert result["FR"]["output_vat"] == Decimal("40.00")
    assert result["FR"]["input_vat"] == Decimal("0.00")
    assert result["FR"]["vat_to_be_paid"] == Decimal("40.00")


def test_read_transactions_from_csv(tmp_path: Path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "\n".join(
            [
                "jurisdiction,transaction_type,net_amount,vat_rate",
                "DE,sale,100.00,0.19",
                "DE,purchase,20.00,0.19",
            ]
        ),
        encoding="utf-8",
    )

    transactions = read_transactions_from_csv(csv_path)
    assert len(transactions) == 2
    assert transactions[0].jurisdiction == "DE"
    assert transactions[0].transaction_type == "sale"


def test_cli_json_output(tmp_path: Path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "\n".join(
            [
                "jurisdiction,transaction_type,net_amount,vat_rate",
                "DE,sale,100.00,0.19",
                "DE,purchase,20.00,0.19",
            ]
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "vat_payable.py", str(csv_path), "--format", "json"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["DE"]["vat_to_be_paid"] == "15.20"


def test_invalid_transaction_type_raises(tmp_path: Path):
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "\n".join(
            [
                "jurisdiction,transaction_type,net_amount,vat_rate",
                "DE,refund,100.00,0.19",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid transaction_type"):
        read_transactions_from_csv(csv_path)
