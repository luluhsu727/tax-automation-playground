# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input format

Provide a JSON file containing a list of transactions:

```json
[
  {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
  {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20}
]
```

- `type` can be `sale` or `purchase`.
- `vat_rate` accepts fractional form (`0.20`) and percentage form (`20` or `"20%"`).
- You can also provide explicit `vat_amount` per transaction.

## Run from CLI

```bash
python3 vat_payable.py transactions.json
```

This prints a JSON object with VAT-to-be-paid amounts per jurisdiction.

Example output:

```json
{"DE": "152.00", "FR": "100.00"}
```

## Python API

```python
from vat_payable import generate_vat_to_be_paid_for_each_jurisdiction

result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
```

This API returns `Decimal` amounts by jurisdiction and floors negative net VAT to `0.00`.
