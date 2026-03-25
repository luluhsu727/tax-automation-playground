# tax-automation-playground

Generate VAT payable totals grouped by jurisdiction.

## Usage

```python
from vat_payable import generate_vat_to_be_paid_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "vat_amount": "19.99"},
    {"jurisdiction": "DE", "vat_amount": "10.01"},
    {"jurisdiction": "FR", "net_amount": "100", "vat_rate": "0.20"},
]

result = generate_vat_to_be_paid_by_jurisdiction(transactions)
# {"DE": Decimal("30.00"), "FR": Decimal("20.00")}
```
