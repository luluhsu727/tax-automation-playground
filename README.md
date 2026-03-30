# tax-automation-playground

Generate VAT to be paid for each jurisdiction from a list of transactions.

## VAT payable generator

Run:

```bash
python vat_payable.py --input transactions.json --output vat_summary.json
```

If `--output` is omitted, results are printed to stdout.

### Input format

`transactions.json` should be a JSON array. Each transaction must include:

- `jurisdiction` (required)
- `input_vat` (optional)
- and either:
  - `output_vat`, or
  - `taxable_amount` + `vat_rate`

Example:

```json
[
  {"jurisdiction": "DE", "output_vat": "190.00", "input_vat": "50.00"},
  {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": "0.19"},
  {"jurisdiction": "FR", "output_vat": "50.00", "input_vat": "60.00"}
]
```

### Output format

The output includes:

- per-jurisdiction `output_vat`, `input_vat`, `net_vat`
- `vat_payable` (`max(net_vat, 0)`)
- `vat_credit` (`max(-net_vat, 0)`)
- aggregated totals across all jurisdictions

## Tests

```bash
python -m unittest -v
```
