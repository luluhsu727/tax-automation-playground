# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction-level inputs.

## VAT payable by jurisdiction

Use `vat_payable.py` with a CSV input file:

```bash
python3 vat_payable.py transactions.csv
```

### Required CSV columns

- `jurisdiction` - country or tax region code/name
- `kind` - one of `sale`, `sales`, `output`, `purchase`, `purchases`, `input`
- `net_amount` - net transaction amount (used with `vat_rate`)
- `vat_rate` - VAT rate (supports `0.2`, `20`, or `20%`)

### Optional CSV column

- `vat_amount` - explicit VAT amount. If present, this is used instead of
  `net_amount * vat_rate`.

### Output

The script prints JSON keyed by jurisdiction with:

- `output_vat`
- `input_vat`
- `net_vat` (`output_vat - input_vat`)
- `vat_to_be_paid` (non-negative amount due)
- `vat_credit` (non-negative recoverable amount when net is negative)
