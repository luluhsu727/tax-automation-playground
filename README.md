# tax-automation-playground

Generate VAT to be paid for each jurisdiction.

## VAT payable rule

For each jurisdiction:

`VAT payable = output VAT (sales) - input VAT (purchases)`

## Python implementation

Function:

- `src.vat_payable.calculate_vat_payable_by_jurisdiction(transactions)`

Expected transaction fields:

- `jurisdiction` (string)
- `vat_amount` (number)
- `type` or `transaction_type` (`sale`/`output` or `purchase`/`input`)

### Example

```python
from src.vat_payable import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "vat_amount": 190.0},
    {"jurisdiction": "DE", "type": "purchase", "vat_amount": 40.0},
    {"jurisdiction": "FR", "transaction_type": "output", "vat_amount": 90.0},
]

print(calculate_vat_payable_by_jurisdiction(transactions))
# {'DE': Decimal('150.00'), 'FR': Decimal('90.00')}
```

## Run tests

```bash
pytest -q
```
