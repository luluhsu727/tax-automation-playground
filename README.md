# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## VAT payable logic

For each jurisdiction:

- **Output VAT** = sum of VAT from sale/output transactions
- **Input VAT** = sum of VAT from purchase/input/expense transactions
- **VAT payable** = `output_vat - input_vat`

## Input format

Provide a JSON file containing either:

1. A list of transaction objects, or
2. An object with a `transactions` list.

Each transaction must include:

- `jurisdiction` (string)
- `type` (string): one of sale/output aliases or purchase/input aliases
- and either:
  - `vat_amount`, or
  - both `amount` and `vat_rate` (VAT is computed as `amount * vat_rate`)

### Example input (`sample_transactions.json`)

```json
{
  "transactions": [
    { "jurisdiction": "DE", "type": "sale", "vat_amount": 120.0 },
    { "jurisdiction": "DE", "type": "purchase", "vat_amount": 25.0 },
    { "jurisdiction": "FR", "type": "sale", "amount": 100.0, "vat_rate": 0.20 },
    { "jurisdiction": "FR", "type": "expense", "amount": 20.0, "vat_rate": 0.20 }
  ]
}
```

## Run

```bash
python vat_payable.py sample_transactions.json
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```
