import csv
import subprocess
import sys
from pathlib import Path


def test_vat_payable_cli_generates_jurisdiction_totals(tmp_path) -> None:
    input_path = tmp_path / "transactions.csv"
    output_path = tmp_path / "vat_payable.csv"

    input_path.write_text(
        "\n".join(
            [
                "jurisdiction,transaction_type,net_amount,vat_rate,vat_amount",
                "DE,sale,1000,0.19,",
                "DE,purchase,400,0.19,",
                "FR,sale,500,0.20,",
                "FR,purchase,700,0.20,",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "vat_payable.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows == [
        {"jurisdiction": "DE", "vat_payable": "114.00"},
        {"jurisdiction": "FR", "vat_payable": "-40.00"},
    ]
