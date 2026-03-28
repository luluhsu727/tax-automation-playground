# tax-automation-playground

Generate VAT payable by jurisdiction from transaction data.

## VAT payable rule

For each jurisdiction:

`VAT payable = max(output VAT - input VAT, 0)`

## Input format

Provide a CSV with at least:

- `jurisdiction`
- `transaction_type` (`sale`/`output`/`collected` or `purchase`/`input`/`deductible`)
- either:
  - `vat_amount`
  - or both `net_amount` and `vat_rate` (rate can be `0.2` or `20`)

## Usage

```bash
python vat_payable.py transactions.csv
```

Output defaults to JSON:

```json
{
  "DE": "16.70",
  "UK": "15.00"
}
```

CSV output:

```bash
python vat_payable.py transactions.csv --format csv
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
