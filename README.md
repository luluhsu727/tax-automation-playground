# tax-automation-playground

Generate VAT to be paid for each jurisdiction using `generate_vat_payable_by_jurisdiction`.

## Example

```python
from vat import Transaction, generate_vat_payable_by_jurisdiction

transactions = [
    Transaction.build("DE", "sale", "1000.00", "0.19"),
    Transaction.build("DE", "purchase", "200.00", "0.19"),
    Transaction.build("FR", "sale", "500.00", "0.20"),
    Transaction.build("FR", "purchase", "700.00", "0.20"),
]

result = generate_vat_payable_by_jurisdiction(transactions)
# {
#   "DE": Decimal("152.00"),
#   "FR": Decimal("-40.00"),
# }
```

Rules:
- Sale transactions add output VAT.
- Purchase transactions subtract input VAT.
- Values are rounded half-up to cents.
- Negative totals indicate recoverable VAT credit.
