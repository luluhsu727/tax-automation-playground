# tax-automation-playground

Simple utilities for tax automation tasks.

## VAT payable by jurisdiction

`generate_vat_payable_by_jurisdiction` groups transactions by jurisdiction and
computes:

- `output_vat` (VAT on sales)
- `input_vat` (VAT on purchases)
- `net_vat = output_vat - input_vat`
- `vat_payable` (when net VAT is positive)
- `vat_credit` (when net VAT is negative)

Example:

```python
from decimal import Decimal
from tax_automation import Transaction, generate_vat_payable_by_jurisdiction

transactions = [
    Transaction(jurisdiction="FR", net_amount=Decimal("1000"), vat_rate=Decimal("0.20"), transaction_type="sale"),
    Transaction(jurisdiction="FR", net_amount=Decimal("200"), vat_rate=Decimal("0.20"), transaction_type="purchase"),
]

result = generate_vat_payable_by_jurisdiction(transactions)
print(result["FR"].vat_payable)  # Decimal("160.00")
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
