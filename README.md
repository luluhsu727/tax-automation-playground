# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## How it works

`vat_payable.py` aggregates VAT by jurisdiction:

- **Output VAT**: VAT collected on `sale` transactions
- **Input VAT**: VAT paid on `purchase` transactions
- **VAT payable**: `output_vat - input_vat`

Each transaction must include:

- `jurisdiction` (string)
- `type` (`sale` or `purchase`)
- Either:
  - `vat_amount`, or
  - both `net_amount` and `vat_rate` (accepts `0.20` or `20`)

## Run

```bash
python vat_payable.py transactions.json --pretty
```

Input file must be a JSON array, for example:

```json
[
  {"jurisdiction": "DE", "type": "sale", "net_amount": 100, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "vat_amount": 5.25},
  {"jurisdiction": "FR", "type": "sale", "net_amount": 200, "vat_rate": 20}
]
```
