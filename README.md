# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Usage

1. Create an input JSON file:

```json
{
  "default_vat_rates": {
    "DE": 0.19,
    "FR": 0.20
  },
  "transactions": [
    {"jurisdiction": "DE", "net_amount": 1000, "transaction_type": "sale"},
    {"jurisdiction": "DE", "net_amount": 100, "transaction_type": "refund"},
    {"jurisdiction": "FR", "net_amount": 500, "transaction_type": "sale"}
  ]
}
```

2. Run:

```bash
python3 vat_payable.py --input input.json
```

Output:

```json
{
  "total_vat_payable": "271.00",
  "vat_payable_by_jurisdiction": {
    "DE": "171.00",
    "FR": "100.00"
  }
}
```

## Test

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
