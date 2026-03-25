# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transactional data.

## Usage

```python
from vat_payable import vat_to_be_paid_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19", "kind": "sale"},
    {"jurisdiction": "DE", "amount": "40.00", "vat_rate": "0.19", "kind": "purchase"},
    {"jurisdiction": "FR", "amount": "50.00", "vat_rate": "0.20", "kind": "purchase"},
]

payable = vat_to_be_paid_by_jurisdiction(transactions)
# {'DE': Decimal('11.40'), 'FR': Decimal('0.00')}
```

## Tests

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```
