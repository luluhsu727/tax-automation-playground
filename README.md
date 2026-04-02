# tax-automation-playground

Generate VAT totals and VAT payable per jurisdiction from transaction data.

## What this does

The calculator groups transactions by `jurisdiction` and computes:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `net_vat`: `output_vat - input_vat`
- `vat_payable`: positive part of `net_vat`
- `vat_refundable`: negative part of `net_vat` converted to a positive number

## Input format

Provide a JSON array of transaction objects. Each transaction must include:

- `jurisdiction` (string)
- `type` (`"sale"` or `"purchase"`)

And either:

- `vat_amount` (explicit VAT amount), or
- `amount` and `vat_rate`

`vat_rate` can be a fraction (`0.2`) or percentage (`20`).

Example:

```json
[
  { "jurisdiction": "FR", "type": "sale", "amount": 100, "vat_rate": 20 },
  { "jurisdiction": "FR", "type": "purchase", "amount": 30, "vat_rate": 20 },
  { "jurisdiction": "DE", "type": "sale", "vat_amount": 19.0 },
  { "jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 19 }
]
```

## Run

```bash
python vat_calculator.py example_transactions.json
```

## Test

```bash
python -m unittest -v
```
