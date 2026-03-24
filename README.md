# tax-automation-playground

Generate VAT payable totals for each jurisdiction from transaction CSV data.

## VAT payable by jurisdiction

Run:

```bash
python3 jurisdiction_vat_payable.py \
  --input sample_transactions.csv \
  --output vat_payable_by_jurisdiction.csv
```

Input CSV must include:

- a jurisdiction/country column (`jurisdiction` or `country`)
- a taxable amount column (`taxable_amount`, `net_amount`, `revenue`, or `amount`)
- optionally, a VAT rate column (`vat_rate` or `rate`)

If `vat_rate` is not provided in input rows, default rates are used:

- DE: 0.19
- FR: 0.20
- ES: 0.21
- IT: 0.22

Output CSV columns:

- `jurisdiction`
- `total_taxable_amount`
- `total_vat_payable`
- `effective_vat_rate`
