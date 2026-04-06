# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## VAT payable rule

For each jurisdiction:

`vat_payable = output_vat_on_sales - input_vat_on_purchases`

## Python API

```python
from vat_automation import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "amount": "1000", "vat_rate": "0.19"},
    {"jurisdiction": "DE", "type": "purchase", "amount": "100", "vat_rate": "0.19"},
    {"jurisdiction": "FR", "is_purchase": False, "vat_amount": "40.00"},
]

result = generate_vat_payable_by_jurisdiction(transactions)
# {"DE": Decimal("171.00"), "FR": Decimal("40.00")}
```

### Supported transaction fields

- `jurisdiction` (required)
- Either:
  - `vat_amount`, or
  - `amount` + `vat_rate`
- Direction:
  - `is_purchase` (`True` purchase, `False` sale), or
  - `type` (supported sale/purchase aliases)
