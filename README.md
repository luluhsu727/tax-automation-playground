# tax-automation-playground

Generate VAT to be paid for each jurisdiction.

## Usage

Create a JSON file containing transactions:

```json
[
  {
    "jurisdiction": "DE",
    "transaction_type": "sale",
    "amount": "1000.00",
    "vat_rate": "0.19"
  },
  {
    "jurisdiction": "DE",
    "transaction_type": "purchase",
    "amount": "200.00",
    "vat_rate": "0.19"
  },
  {
    "jurisdiction": "FR",
    "transaction_type": "sale",
    "vat_amount": "50.00",
    "amount": "250.00"
  }
]
```

Run:

```bash
python vat_payable.py --input transactions.json
```

Output:

```json
{
  "jurisdictions": {
    "DE": {
      "output_vat": "190.00",
      "input_vat": "38.00",
      "vat_payable": "152.00"
    },
    "FR": {
      "output_vat": "50.00",
      "input_vat": "0.00",
      "vat_payable": "50.00"
    }
  }
}
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
