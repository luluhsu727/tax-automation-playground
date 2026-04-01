# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## What this project computes

For each jurisdiction, the script aggregates:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `net_vat`: `output_vat - input_vat`
- `vat_payable`: max(`net_vat`, 0)
- `vat_refundable`: max(-`net_vat`, 0)

## Input format

Use a JSON file containing either:

1. A list of transaction objects, or
2. An object with a `transactions` list.

Each transaction requires:

- `jurisdiction` (string)
- `type` (`sale`/`sales`/`output` or `purchase`/`purchases`/`input`)
- Either:
  - `vat_amount`, or
  - `net_amount` + `vat_rate`

Example:

```json
[
  { "jurisdiction": "DE", "type": "sale", "net_amount": "100.00", "vat_rate": "0.19" },
  { "jurisdiction": "DE", "type": "purchase", "vat_amount": "9.50" },
  { "jurisdiction": "FR", "type": "sale", "vat_amount": "20.00" },
  { "jurisdiction": "FR", "type": "purchase", "vat_amount": "40.00" }
]
```

## Run

```bash
python vat_payable.py input.json
```

Optional output file:

```bash
python vat_payable.py input.json --output summary.json
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
