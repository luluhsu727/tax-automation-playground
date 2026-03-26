# tax-automation-playground

Generate VAT to be paid for each jurisdiction from taxable transactions.

## VAT calculation

Use `vat_to_be_paid_by_jurisdiction` from `vat.py`.

```python
from decimal import Decimal
from vat import Transaction, vat_to_be_paid_by_jurisdiction

transactions = [
    Transaction("DE", Decimal("100.00"), Decimal("0.19"), "sale"),
    Transaction("DE", Decimal("40.00"), Decimal("0.19"), "purchase"),
    Transaction("FR", Decimal("200.00"), Decimal("0.20"), "sale"),
]

result = vat_to_be_paid_by_jurisdiction(transactions)
print(result["DE"]["vat_payable"])  # 11.40
```

Returned structure per jurisdiction:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `vat_payable`: `output_vat - input_vat`
- `vat_credit`: positive amount when `vat_payable` is negative, else `0.00`

## Run tests

```bash
pytest -q
```
