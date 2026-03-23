# AGENTS.md

## Cursor Cloud specific instructions

This is a Python-only repository with CLI scripts for EU VAT reconciliation. There is no web app, database, or Docker setup.

### Services

| Script | Description | Dependencies |
|---|---|---|
| `vat_check.py` | CSV-in/CSV-out VAT checker (stdlib only) | None beyond Python 3.10+ |
| `vat_check_small.py` | pandas-based VAT reconciliation outputting Excel | `pandas`, `openpyxl` |

### Running

- **Lint:** `flake8 vat_check.py vat_check_small.py --max-line-length=120`
- **Type check:** `mypy vat_check.py vat_check_small.py --ignore-missing-imports`
- **Tests:** `pytest tests/ -v`
- **vat_check.py:** `python3 vat_check.py --input <csv> --output <out.csv> --summary-output <summary.csv>`
- **vat_check_small.py:** `python3 vat_check_small.py --input <csv> --output <out.xlsx>`

### Gotchas

- `vat_check.py` uses only Python stdlib; `vat_check_small.py` requires `pandas` and `openpyxl`.
- Sample CSV files (`sample_transactions.csv`, `eu_transactions.csv`) are provided in the repo root for testing.
- The scripts expect CSV input with columns: `transaction_id`, `country`, `revenue`, `vat_collected`.
- `vat_check_small.py` will raise `ValueError` for unsupported country codes (only DE, FR, ES, IT are supported); `vat_check.py` flags them instead.
- pip packages install to `~/.local/bin`; ensure `PATH` includes that directory.
