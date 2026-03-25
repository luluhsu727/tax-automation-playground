# tax-automation-playground

## VAT payable by jurisdiction

Use `vat_payable.py` to generate net VAT payable for each jurisdiction from a JSON
array of transactions.

### Input format

Each record must include:

- `jurisdiction` (string)
- `transaction_type` (or `type`) as `sale` or `purchase`
- either:
  - `vat_amount`, or
  - both `net_amount` and `vat_rate` (`0.2` or `20` are both accepted)

Example `transactions.json`:

```json
[
  {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "25.00"},
  {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "10.00"},
  {"jurisdiction": "FR", "transaction_type": "sale", "net_amount": "100.00", "vat_rate": 20},
  {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": "24.00"}
]
```

### Run

```bash
python3 vat_payable.py transactions.json
```

Output:

```text
DE: 15.00
FR: -4.00
```

Optional flags:

- `--floor-at-zero` to clamp negative jurisdiction totals to `0.00`
- `--json` to output a JSON object
