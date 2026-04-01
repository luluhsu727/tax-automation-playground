import csv
from pathlib import Path

from vat_payable.io import load_transactions_from_csv, run_cli


def test_load_transactions_from_csv_requires_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("jurisdiction,amount\nDE,100\n", encoding="utf-8")

    try:
        load_transactions_from_csv(path)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "missing required columns" in str(exc).lower()


def test_run_cli_writes_csv_report(tmp_path: Path) -> None:
    input_path = tmp_path / "transactions.csv"
    output_path = tmp_path / "report.csv"
    input_path.write_text(
        "jurisdiction,amount,vat_rate,transaction_type,vat_amount\n"
        "DE,1000,19,sale,\n"
        "DE,200,19,purchase,\n"
        "FR,800,20,sale,160\n",
        encoding="utf-8",
    )

    exit_code = run_cli(
        [
            "--input",
            str(input_path),
            "--format",
            "csv",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {
            "jurisdiction": "DE",
            "output_vat": "190.0",
            "input_vat": "38.0",
            "vat_payable": "152.0",
        },
        {
            "jurisdiction": "FR",
            "output_vat": "160.0",
            "input_vat": "0.0",
            "vat_payable": "160.0",
        },
    ]
