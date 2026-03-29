# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input format

Provide a CSV with the following columns:

- `jurisdiction` (e.g. `DE`, `FR`)
- `transaction_type` (`sale` or `purchase`)
- `net_amount` (decimal)
- `vat_rate` (decimal, e.g. `0.20` for 20%)

Example:

```csv
jurisdiction,transaction_type,net_amount,vat_rate
DE,sale,100.00,0.19
DE,purchase,20.00,0.19
FR,sale,200.00,0.20
```

## Run

```bash
python vat_payable.py transactions.csv
```

Output (JSON):

```json
{
  "DE": {
    "input_vat": "3.80",
    "output_vat": "19.00",
    "vat_to_be_paid": "15.20"
  },
  "FR": {
    "input_vat": "0.00",
    "output_vat": "40.00",
    "vat_to_be_paid": "40.00"
  }
}
```

Optional table output:

```bash
python vat_payable.py transactions.csv --format table
```

## Tests

```bash
python -m pytest -q
```
