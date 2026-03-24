# tax-automation-playground

Generate VAT payable (or reclaim position) by jurisdiction from transaction data.

## VAT payable by jurisdiction

This repository includes a simple Python module and CLI to calculate VAT to be paid
for each jurisdiction.

- `sale` transactions add output VAT
- `purchase` transactions subtract input VAT credits

### Transaction schema

Each transaction is a JSON object with:

- `jurisdiction` (string, non-empty)
- `amount_ex_vat` (number or string)
- `vat_rate` (number or string, e.g. `0.20` for 20%)
- `transaction_type` (`sale` or `purchase`)

### Example input (`transactions.json`)

```json
[
  {
    "jurisdiction": "DE",
    "amount_ex_vat": "100.00",
    "vat_rate": "0.19",
    "transaction_type": "sale"
  },
  {
    "jurisdiction": "DE",
    "amount_ex_vat": "50.00",
    "vat_rate": "0.19",
    "transaction_type": "purchase"
  },
  {
    "jurisdiction": "FR",
    "amount_ex_vat": "200.00",
    "vat_rate": "0.20",
    "transaction_type": "sale"
  }
]
```

### Run from CLI

```bash
python vat_payable.py transactions.json
```

Example output:

```json
{
  "DE": "9.50",
  "FR": "40.00"
}
```

### Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
