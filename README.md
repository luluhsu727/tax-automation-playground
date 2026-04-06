# tax-automation-playground

Generate VAT to be paid per jurisdiction from taxable transactions.

## Usage

```python
from decimal import Decimal
from vat_payable import Transaction, generate_vat_payable_by_jurisdiction

transactions = [
    Transaction("UK", Decimal("100.00"), "sale"),
    Transaction("UK", Decimal("30.00"), "purchase"),
    Transaction("DE", Decimal("100.00"), "sale"),
]

result = generate_vat_payable_by_jurisdiction(
    transactions,
    jurisdiction_vat_rates={"UK": "0.20", "DE": "0.19"},
)

print(result["UK"].vat_payable)  # Decimal("14.00")
```
