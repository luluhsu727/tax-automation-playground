# tax-automation-playground

Generate VAT payable totals for each jurisdiction from transaction data.

## VAT payable by jurisdiction

### Input format

Provide a CSV with these required columns:

- `jurisdiction` (e.g., `DE`, `FR`)
- `transaction_type` (`sale` or `purchase`)
- `net_amount` (taxable base amount)
- `vat_rate` (for example `0.19`)

### Generate jurisdiction VAT payable output

```bash
python3 -m tax.cli --input transactions.csv --output vat_payable_by_jurisdiction.csv
```

### Output columns

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable` (computed as `output_vat - input_vat`)
