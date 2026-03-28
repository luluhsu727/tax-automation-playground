# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## Run example

```bash
python3 vat_payable.py input.json
```

Where `input.json` is shaped like:

```json
{
  "transactions": [
    {
      "jurisdiction": "DE",
      "transaction_type": "sale",
      "amount": 1000,
      "vat_rate": 0.19
    },
    {
      "jurisdiction": "DE",
      "transaction_type": "purchase",
      "amount": 400,
      "vat_rate": 0.19
    }
  ]
}
```

Output contains:

```json
{
  "vat_payable_by_jurisdiction": {
    "DE": 114.0
  }
}
```
