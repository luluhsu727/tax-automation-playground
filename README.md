# tax-automation-playground

Generate the VAT to be paid for each jurisdiction.

## Usage

Provide transactions as a JSON array on stdin:

```bash
python vat_payable.py <<'JSON'
[
  {"jurisdiction": "DE", "type": "sale", "amount": 100.00, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 20.00, "vat_rate": 0.19},
  {"jurisdiction": "FR", "vat_collected": 50.00, "vat_paid": 10.00}
]
JSON
```

Output:

```json
{
  "DE": "15.20",
  "FR": "40.00"
}
```

## Rules

- If `vat_collected`/`vat_paid` are present, net VAT is `vat_collected - vat_paid`.
- Otherwise, for:
  - `type = sale` => VAT effect is `amount * vat_rate`
  - `type = purchase` => VAT effect is `-(amount * vat_rate)`
- Totals are grouped by `jurisdiction` and rounded to 2 decimals (half-up).

## Tests

```bash
python -m unittest -v
```
