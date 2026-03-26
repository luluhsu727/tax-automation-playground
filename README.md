# tax-automation-playground

Generate VAT payable totals per jurisdiction from transaction data.

## VAT payable by jurisdiction

Use `vat_payable.py` to aggregate output VAT, input VAT, net VAT, payable VAT, and refundable VAT for each jurisdiction.

### Input format

Provide a CSV with:

- `jurisdiction` (required)
- `transaction_type` (required): `sale`/`output` or `purchase`/`input`
- either:
  - `vat_amount`
  - or `net_amount` + `vat_rate` (accepts both `0.20` and `20`)

### Example

```csv
jurisdiction,transaction_type,vat_amount
DE,sale,120.00
DE,purchase,20.00
FR,sale,40.50
FR,purchase,70.10
```

Run:

```bash
python vat_payable.py transactions.csv
```

Output (JSON):

```json
{
  "DE": {
    "input_vat": "20.00",
    "net_vat": "100.00",
    "output_vat": "120.00",
    "vat_payable": "100.00",
    "vat_refundable": "0.00"
  },
  "FR": {
    "input_vat": "70.10",
    "net_vat": "-29.60",
    "output_vat": "40.50",
    "vat_payable": "0.00",
    "vat_refundable": "29.60"
  }
}
```

CSV output is also supported:

```bash
python vat_payable.py transactions.csv --format csv --output vat_summary.csv
```

### Tests

```bash
python -m unittest -v
```
