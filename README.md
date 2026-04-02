# tax-automation-playground

Generate VAT payable (`output VAT - input VAT`) for each jurisdiction from a CSV of transactions.

## Usage

Input CSV columns:

- `jurisdiction` (e.g. `DE`, `FR`, `GB`)
- `transaction_type` (`sale` or `purchase`)
- `amount`
- `vat_rate` (decimal `0.20` or percentage `20`)
- `amount_includes_vat` (optional, `true`/`false`)

Run:

```bash
python vat_payable.py --input transactions.csv --output vat_payable_by_jurisdiction.csv
```

Output CSV columns:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
