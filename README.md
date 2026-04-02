# tax-automation-playground

## VAT payable by jurisdiction

This repository includes a helper to generate the VAT to be paid for each
jurisdiction:

`calculate_vat_payable_by_jurisdiction(transactions, decimal_places=2)`

- Input: iterable of transaction dictionaries with:
  - `jurisdiction` (required), and either:
    - `vat_amount`, or
    - both `amount` and `vat_rate` (e.g. `0.20` for 20%)
- Output: dictionary of `jurisdiction -> Decimal(total_vat_payable)`

### Example

```python
from vat import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19"},
    {"jurisdiction": "DE", "vat_amount": "1.50"},
    {"jurisdiction": "FR", "amount": "50", "vat_rate": "0.20"},
]

totals = calculate_vat_payable_by_jurisdiction(transactions)
# {"DE": Decimal("20.50"), "FR": Decimal("10.00")}
```

### Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
