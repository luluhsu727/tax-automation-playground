import json
import subprocess
import sys


def test_cli_outputs_vat_payable_by_jurisdiction(tmp_path) -> None:
    payload = [
        {"jurisdiction": "DE", "type": "sale", "vat_amount": "100.50"},
        {"jurisdiction": "DE", "type": "purchase", "vat_amount": "50.25"},
        {"jurisdiction": "NL", "type": "sale", "amount": "1000", "vat_rate": "21"},
    ]

    input_file = tmp_path / "transactions.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")

    process = subprocess.run(
        [sys.executable, "-m", "vat_payable.cli", str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(process.stdout) == {"DE": "50.25", "NL": "210.00"}
