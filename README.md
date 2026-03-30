# tax-automation-playground

Simple utilities for tax automation tasks.

## VAT payable by jurisdiction

Use `generate_vat_payable_by_jurisdiction` to compute output VAT, input VAT,
and net VAT payable for each jurisdiction.

```python
from vat_calculator import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": "100.00", "transaction_type": "sale"},
    {"jurisdiction": "DE", "amount": "40.00", "transaction_type": "purchase"},
    {"jurisdiction": "FR", "amount": "80.00", "transaction_type": "sale"},
]
rates = {"DE": "0.19", "FR": "0.20"}

summary = generate_vat_payable_by_jurisdiction(transactions, rates)
# {
#   "DE": {"output_vat": Decimal("19.00"), "input_vat": Decimal("7.60"), "vat_payable": Decimal("11.40")},
#   "FR": {"output_vat": Decimal("16.00"), "input_vat": Decimal("0.00"), "vat_payable": Decimal("16.00")},
# }
```
