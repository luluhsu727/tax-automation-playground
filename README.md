# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## Run

Create a JSON file with a list of transactions:

```json
[
  {"jurisdiction": "DE", "direction": "sale", "amount": "1000", "vat_rate": "0.19"},
  {"jurisdiction": "DE", "direction": "purchase", "amount": "200", "vat_rate": "0.19"},
  {"jurisdiction": "FR", "direction": "sale", "vat_amount": "80"},
  {"jurisdiction": "FR", "direction": "input", "vat_amount": "120"}
]
```

Then run:

```bash
python vat_payable.py transactions.json
```

Example output:

```json
{
  "DE": {
    "input_vat": "38.00",
    "net_vat": "152.00",
    "output_vat": "190.00",
    "vat_credit": "0.00",
    "vat_payable": "152.00"
  },
  "FR": {
    "input_vat": "120.00",
    "net_vat": "-40.00",
    "output_vat": "80.00",
    "vat_credit": "40.00",
    "vat_payable": "0.00"
  }
}
```

## Testing

```bash
python -m unittest discover -s tests
```
