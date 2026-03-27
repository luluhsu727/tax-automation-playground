# tax-automation-playground

## VAT payable by jurisdiction

This repository includes a utility to generate VAT totals per jurisdiction:

- taxable sales
- taxable purchases
- output VAT (from sales)
- input VAT (from purchases)
- VAT payable (`output_vat - input_vat`)

### Usage

```python
from vat_payable import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "amount": "100.00"},
    {"jurisdiction": "DE", "type": "purchase", "amount": "25.00"},
    {"jurisdiction": "FR", "type": "sale", "amount": "200.00", "vat_rate": 10},
]

vat_rates_by_jurisdiction = {
    "DE": 0.19,
    "FR": 0.20,
}

report = calculate_vat_payable_by_jurisdiction(
    transactions, vat_rates_by_jurisdiction
)
```

`vat_rate` accepts either ratio format (`0.20`) or percentage format (`20`).
