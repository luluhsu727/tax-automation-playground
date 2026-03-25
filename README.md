# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction-level inputs.

## VAT payable calculator

This repository includes `vat_payable.py`, which computes:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `vat_payable`: `output_vat - input_vat`

## Input format

Provide a JSON array of transactions. Each transaction requires:

- `jurisdiction` (string)
- `transaction_type` (`"sale"` or `"purchase"`)
- Either:
  - `vat_amount`, or
  - both `taxable_amount` and `vat_rate`

`vat_rate` can be decimal (`0.2`) or percentage (`20`).

Example:

```json
[
  {"jurisdiction": "DE", "transaction_type": "sale", "taxable_amount": 100, "vat_rate": 0.19},
  {"jurisdiction": "DE", "transaction_type": "purchase", "taxable_amount": 20, "vat_rate": 0.19},
  {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": "10.00"}
]
```

## Run

Table output:

```bash
python vat_payable.py transactions.json
```

JSON output:

```bash
python vat_payable.py transactions.json --format json
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
