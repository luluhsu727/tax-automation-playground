# tax-automation-playground

## VAT payable by jurisdiction

This repository includes a small utility to generate **net VAT payable per jurisdiction**.

### Rule used

For each jurisdiction:

- `sale` transactions add VAT (output VAT)
- `purchase` transactions subtract VAT (input VAT)
- net result = **VAT to be paid** (or reclaimed if negative)

### Input format

Provide a JSON array where each item contains:

- `jurisdiction` (required)
- `kind` (required): `"sale"` or `"purchase"`
- either:
  - `vat_amount`
- or:
  - `taxable_amount` (or `amount`) and `vat_rate`

Example:

```json
[
  { "jurisdiction": "DE", "kind": "sale", "taxable_amount": "100.00", "vat_rate": "0.19" },
  { "jurisdiction": "DE", "kind": "purchase", "taxable_amount": "40.00", "vat_rate": "0.19" },
  { "jurisdiction": "FR", "kind": "sale", "vat_amount": "20.00" },
  { "jurisdiction": "FR", "kind": "purchase", "vat_amount": "5.00" }
]
```

### Run

```bash
python3 vat_calculator.py input.json
```

Example output:

```json
{
  "DE": "11.40",
  "FR": "15.00"
}
```

### Tests

```bash
python3 -m unittest -v
```
