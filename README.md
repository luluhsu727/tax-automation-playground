# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## What this project now provides

- `vat_payable.py`:
  - `generate_vat_payable_by_jurisdiction(transactions)` for programmatic use.
  - CLI: read transactions from CSV and write a per-jurisdiction VAT summary CSV.
- `tests/test_vat_payable.py`: unit tests for core calculation rules.
- `sample_transactions.csv`: sample input data.

## VAT calculation rules

Per jurisdiction:

- `output_vat`: sum of VAT from `sale` / `output` transactions.
- `input_vat`: sum of VAT from `purchase` / `input` transactions.
- `net_vat = output_vat - input_vat`
- `vat_payable = max(net_vat, 0)`
- `vat_credit = max(-net_vat, 0)`

VAT is taken from:

1. `vat_amount` when provided, otherwise
2. `amount * vat_rate`

All monetary fields are rounded half-up to 2 decimal places.

## Input CSV format

Expected columns:

- `jurisdiction` (required)
- `transaction_type` (required: `sale`, `output`, `purchase`, or `input`)
- `vat_amount` (optional)
- `amount` and `vat_rate` (optional alternative to `vat_amount`)

## Usage

Run the CLI:

```bash
python3 vat_payable.py sample_transactions.csv vat_summary.csv
```

Run tests:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
