# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

This is a Python CLI project for EU VAT reconciliation. Two scripts exist on separate feature branches:

- `vat_check.py` (branch `cursor/csv-upload-and-analysis-f308`) — stdlib-only CSV processor. Supports DE/FR/ES VAT rates.
- `vat_check_small.py` (branch `cursor/eu-vat-reconciliation-d217`) — pandas-based, outputs Excel `.xlsx`. Supports DE/FR/ES/IT VAT rates.

### Dependencies

- Python 3.10+ (3.12 available in the VM)
- `pandas`, `openpyxl` — required by `vat_check_small.py`
- `ruff` — linter/formatter (installed as dev tool)
- All installed via: `pip install -r requirements.txt` (for runtime) and `pip install ruff` (for dev)

### Running the scripts

Both scripts accept `--input`, `--output` args. Sample data files are provided:

```bash
# vat_check.py (stdlib CSV variant)
python3 vat_check.py --input sample_transactions.csv --output vat_check_results.csv --summary-output vat_reconciliation_summary.csv

# vat_check_small.py (pandas/Excel variant)
python3 vat_check_small.py --input eu_transactions.csv --output vat_report.xlsx
```

### Linting

```bash
ruff check .
ruff format --check .
```

Note: `vat_check_small.py` (from the upstream branch) has minor formatting issues that `ruff format` would fix. This is a pre-existing condition.

### Gotchas

- `vat_check.py` defaults `--input` to a hardcoded path under `/home/ubuntu/.cursor/projects/workspace/uploads/`. Always pass `--input` explicitly.
- `vat_check_small.py` has fallback path resolution logic; providing `--input` explicitly avoids surprises.
- No automated test suite exists yet. Validation is done by running the scripts with sample CSV data and inspecting output.
