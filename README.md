# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction records.

## Input format

Provide a JSON array of records. Each record must include:

- `jurisdiction`: jurisdiction code/name
- `transaction_type` (or `type`): `sale` or `purchase`

VAT can be supplied in either form:

1. Direct VAT amount:
   - `vat_amount`
2. Derived VAT:
   - `net_amount`
   - `vat_rate` (e.g., `0.2` or `20`)

## Run

```bash
python3 vat_payable.py path/to/transactions.json
```

Options:

- `--floor-at-zero`: clamp negative net VAT to `0.00`
- `--json`: output JSON

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
