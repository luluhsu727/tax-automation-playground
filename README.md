# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction rows.

## VAT payable rule

For each jurisdiction:

```
VAT payable = VAT on sales - VAT on purchases
```

Each transaction must include:

- `jurisdiction` (string)
- `type` (`sale` or `purchase`)
- `amount` (taxable amount)
- `vat_rate` (decimal, e.g. `0.20` for 20%)

## Usage

Input can be provided through a JSON file:

```bash
python vat_calculator.py --input transactions.json
```

Or through stdin:

```bash
cat transactions.json | python vat_calculator.py
```

Example input:

```json
[
  {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
  {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20}
]
```

Example output:

```json
{
  "DE": "152.00",
  "FR": "100.00"
}
```
