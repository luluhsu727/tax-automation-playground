# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input format

Use a CSV file with at least:

- `jurisdiction` (for example `DE`, `FR`)
- `transaction_type` (`sale` or `purchase`)

And either:

- `vat_amount` directly, or
- `amount` and `vat_rate` (for example `100` and `0.20`)

## Example CSV

```csv
jurisdiction,transaction_type,amount,vat_rate
DE,sale,100,0.19
DE,purchase,20,0.19
FR,sale,80,0.20
FR,purchase,60,0.20
```

## Run

```bash
python3 vat_payable.py transactions.csv
```

To output JSON:

```bash
python3 vat_payable.py transactions.csv --json
```

## Test

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
