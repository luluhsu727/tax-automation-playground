# tax-automation-playground

Generate VAT payable totals for each jurisdiction from a list of transactions.

## Quick start

Run the unit tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Usage example

```python
from vat_calculator import generate_vat_to_be_paid_for_each_jurisdiction

transactions = [
    {"jurisdiction": "DE", "taxable_amount": "100.00"},
    {"jurisdiction": "DE", "taxable_amount": "50.00"},
    {"jurisdiction": "FR", "taxable_amount": "120.00"},
]

vat_rates = {
    "DE": "0.19",
    "FR": "0.20",
}

vat_by_jurisdiction = generate_vat_to_be_paid_for_each_jurisdiction(
    transactions,
    vat_rates_by_jurisdiction=vat_rates,
)

print(vat_by_jurisdiction)
# {'DE': Decimal('28.50'), 'FR': Decimal('24.00')}
```
