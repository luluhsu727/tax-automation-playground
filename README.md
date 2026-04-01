# tax-automation-playground

Generate VAT payable for each jurisdiction.

## VAT payable logic

For each jurisdiction:

`VAT payable = output VAT from sales - input VAT from purchases`

Negative totals represent a VAT credit/refund position.

## Usage

1. Create a JSON file with an array of transaction records.
2. Run:

```bash
python3 vat_payable.py path/to/transactions.json
```

Each record must include:

- `jurisdiction`
- `kind`: `sale`/`sales`/`output` or `purchase`/`purchases`/`input`
- one of:
  - `vat_amount`, or
  - both `net_amount` and `vat_rate`

Example input:

```json
[
  {"jurisdiction": "DE", "kind": "sale", "vat_amount": "190.00"},
  {"jurisdiction": "DE", "kind": "purchase", "vat_amount": "40.00"},
  {"jurisdiction": "FR", "kind": "sale", "net_amount": "1000.00", "vat_rate": "0.20"},
  {"jurisdiction": "FR", "kind": "purchase", "vat_amount": "240.00"}
]
```

Example output:

```json
{
  "DE": "150.00",
  "FR": "-40.00"
}
```

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
