# tax-automation-playground

Generate VAT payable totals per jurisdiction from transaction records.

## Input format

Each transaction record must include:

- `jurisdiction`
- `transaction_type` (`sale` or `purchase`)
- Either:
  - `vat_amount`, or
  - `net_amount` and `vat_rate` (rate can be `19` or `0.19`)

## Usage

Run from CSV:

```bash
python vat_calculator.py transactions.csv --pretty
```

Expected CSV headers:

```csv
jurisdiction,transaction_type,vat_amount,net_amount,vat_rate
DE,sale,,1000,19
DE,purchase,,200,19
FR,sale,50,,
FR,purchase,80,,
```

## Tests

```bash
python -m unittest -v
```
