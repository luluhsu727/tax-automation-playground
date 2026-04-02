# tax-automation-playground

## VAT payable by jurisdiction

Generate VAT to be paid for each jurisdiction from a transactions CSV:

```bash
python jurisdiction_vat_payable.py --input sample_transactions.csv --output vat_payable_by_jurisdiction.csv
```

Output columns:
- `jurisdiction`
- `total_taxable_amount`
- `total_vat_payable`
- `effective_vat_rate`
