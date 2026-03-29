# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## VAT payable rule

For each jurisdiction:

`vat_payable = output_vat (sales VAT) - input_vat (purchase VAT)`

## Python API

```python
from vat_payable import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": 100, "vat_rate": 0.19, "transaction_type": "sale"},
    {"jurisdiction": "DE", "amount": 50, "vat_rate": 0.19, "transaction_type": "purchase"},
]
print(calculate_vat_payable_by_jurisdiction(transactions))
# {"DE": 9.5}
```

Supported input fields per transaction:

- `jurisdiction` (or `country`)
- `transaction_type`: `sale` or `purchase` (defaults to `sale`)
- either:
  - `vat_amount`, or
  - `amount`/`net_amount` + `vat_rate` (`0.19` or `19`)

## CLI usage

```bash
python3 vat_payable.py transactions.json
```

`transactions.json` must contain an array of transaction objects.

## Run tests

```bash
python3 -m unittest -v
```
