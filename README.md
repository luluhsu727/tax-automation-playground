# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input shape

Pass a JSON array where each transaction includes:

- `jurisdiction` (string): country/region code or name
- `transaction_type` (string):
  - output VAT types: `sale`, `output`, `collected`
  - input VAT types: `purchase`, `input`, `paid`
- VAT value from either:
  - `vat_amount` directly, or
  - `amount` + `vat_rate` (rate can be `19` or `0.19`)

## Run

```bash
python vat_calculator.py transactions.json
```

Optional output file:

```bash
python vat_calculator.py transactions.json --output vat_due.json
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```
