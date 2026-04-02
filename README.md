# tax-automation-playground

Utilities for VAT/tax automation experiments.

## VAT payable by jurisdiction

The `generate_vat_payable_by_jurisdiction` function aggregates output VAT
(`sale`) and input VAT (`purchase`) per jurisdiction, then computes:

```
vat_payable = output_vat - input_vat
```

### Example

```python
from vat_payable import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "net_amount": "100.00", "vat_rate": "19"},
    {"jurisdiction": "DE", "type": "purchase", "net_amount": "40.00", "vat_rate": "19"},
]

result = generate_vat_payable_by_jurisdiction(transactions)
print(result["DE"]["vat_payable"])  # Decimal("11.40")
```
