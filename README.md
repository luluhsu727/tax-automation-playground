# tax-automation-playground

## VAT payable by jurisdiction

Use `calculate_vat_payable_by_jurisdiction` to generate net VAT to be paid per jurisdiction.

```python
from vat import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
    {"jurisdiction": "DE", "type": "purchase", "vat_amount": 50},
    {"jurisdiction": "FR", "type": "output", "vat_amount": 120},
]

result = calculate_vat_payable_by_jurisdiction(transactions)
# {"DE": 140.0, "FR": 120.0}
```

Accepted transaction direction values:
- output side: `sale`, `output`, `output_vat`
- input side: `purchase`, `input`, `input_vat`
