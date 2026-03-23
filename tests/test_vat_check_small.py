"""Tests for vat_check_small.py EU VAT reconciliation."""
from pathlib import Path

import pandas as pd

from vat_check_small import build_vat_tables


def test_build_vat_tables(tmp_path: Path) -> None:
    csv_path = tmp_path / "eu.csv"
    csv_path.write_text(
        "transaction_id,country,revenue,vat_collected\n"
        "EU1,DE,1000,190\n"
        "EU2,FR,500,100\n"
        "EU3,IT,800,176\n"
    )

    transactions, summary = build_vat_tables(csv_path)

    assert len(transactions) == 3
    assert "expected_vat" in transactions.columns
    assert "variance" in transactions.columns

    assert set(summary["country"].tolist()) == {"DE", "FR", "IT"}


def test_anomaly_detection(tmp_path: Path) -> None:
    csv_path = tmp_path / "eu.csv"
    csv_path.write_text(
        "transaction_id,country,revenue,vat_collected\n"
        "EU1,FR,300,58\n"
    )

    transactions, _ = build_vat_tables(csv_path)

    assert bool(transactions.iloc[0]["flag_anomaly"]) is True
    assert transactions.iloc[0]["variance"] == 2.0
