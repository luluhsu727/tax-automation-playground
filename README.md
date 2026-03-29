# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## VAT payable by jurisdiction

Use `calculate_vat_payable_by_jurisdiction` from `vat_payable.py`.

```python
from vat_payable import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "output_vat": 100, "input_vat": 20},
    {"jurisdiction": "DE", "output_vat": 50, "input_vat": 10},
    {"jurisdiction": "FR", "transaction_type": "sale", "amount": 1000, "vat_rate": 0.20},
    {"jurisdiction": "FR", "transaction_type": "purchase", "amount": 200, "vat_rate": 0.20},
]

result = calculate_vat_payable_by_jurisdiction(transactions)

# {
#   "DE": {"output_vat": 150.0, "input_vat": 30.0, "vat_payable": 120.0},
#   "FR": {"output_vat": 200.0, "input_vat": 40.0, "vat_payable": 160.0}
# }
```

### Supported transaction shapes

1. Explicit VAT values:
   - `jurisdiction` (str)
   - `output_vat` (number, optional default 0)
   - `input_vat` (number, optional default 0)

2. Amount/rate with transaction type:
   - `jurisdiction` (str)
   - `transaction_type` (`"sale"` or `"purchase"`)
   - `amount` (number)
   - `vat_rate` (number, e.g. `0.20` for 20%)

### Rule

For each jurisdiction:

`vat_payable = total_output_vat - total_input_vat`
