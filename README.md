# tax-automation-playground

## VAT payable by jurisdiction

Use `vat_check.py` to generate VAT payable totals for each jurisdiction.

### Input CSV requirements

The CSV must include:

- `transaction_id`
- `revenue`
- `vat_collected`
- either `jurisdiction` or `country` (ISO-like code such as `DE`, `FR`)

### Output files

The script writes two CSV outputs:

1. Transaction-level output (default: `vat_check_results.csv`) containing:
   - original columns
   - `vat_rate`
   - `expected_vat`
   - `vat_payable` (`expected_vat - vat_collected`)
2. Jurisdiction summary (default: `vat_payable_by_jurisdiction.csv`) containing:
   - `jurisdiction`
   - `total_revenue`
   - `total_vat_collected`
   - `total_expected_vat`
   - `vat_payable`

### Run

```bash
python3 vat_check.py \
  --input path/to/transactions.csv \
  --output vat_check_results.csv \
  --summary-output vat_payable_by_jurisdiction.csv
```
