# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction-level input data.

## VAT payable by jurisdiction

Use `vat_payable.py` with either JSON or CSV input:

```bash
python3 vat_payable.py transactions.json
python3 vat_payable.py transactions.csv
```

By default, output is a text report with `jurisdiction: vat_to_be_paid`.
Use `--json` for a full VAT breakdown:

```bash
python3 vat_payable.py transactions.csv --json
```

### Supported fields

- `jurisdiction` (required)
- transaction type via one of:
  - `transaction_type`
  - `kind`
  - `type`
  where value is one of: `sale`, `sales`, `output`, `purchase`, `purchases`, `input`
- VAT amount via either:
  - `vat_amount`, or
  - `net_amount` + `vat_rate` (`0.2`, `20`, and `20%` are all accepted)

### Notes

- Net VAT is calculated as: sales VAT - purchase VAT.
- `vat_to_be_paid` is always non-negative.
- Negative net VAT is exposed as `vat_credit` in JSON output.
