# tax-automation-playground

## VAT payable by jurisdiction

Use `calculate_vat_to_be_paid_by_jurisdiction` (or the `generate_*` aliases) from `vat.py`.

Example:

```python
from vat import calculate_vat_to_be_paid_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": "100.00", "vat_rate": 0.19},
    {"jurisdiction": "DE", "amount": "50.00", "vat_rate": 0.19},
    {"jurisdiction": "FR", "amount": "200.00", "vat_rate": 20},  # percentage input
]

result = calculate_vat_to_be_paid_by_jurisdiction(transactions)
# {"DE": Decimal("28.50"), "FR": Decimal("40.00")}
```
