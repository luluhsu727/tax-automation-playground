# tax-automation-playground

Generate net VAT payable for each jurisdiction from sales and purchase transactions.

## VAT payable logic

For each jurisdiction:

`VAT payable = output VAT on sales - input VAT on purchases`

- Positive result: VAT to pay
- Negative result: VAT refund/recoverable position

## Usage

```python
from decimal import Decimal
from vat_calculator import Transaction, calculate_vat_payable_by_jurisdiction

transactions = [
    Transaction("DE", Decimal("1000"), Decimal("19"), "sale"),
    Transaction("DE", Decimal("200"), Decimal("19"), "purchase"),
    Transaction("FR", Decimal("300"), Decimal("20"), "sale"),
    Transaction("FR", Decimal("100"), Decimal("20"), "purchase"),
]

result = calculate_vat_payable_by_jurisdiction(transactions)
print(result)
# {'DE': Decimal('152.00'), 'FR': Decimal('40.00')}
```

## Run tests

```bash
python -m pytest -q
```
