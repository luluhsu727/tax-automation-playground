# tax-automation-playground

Generate VAT to be paid for each jurisdiction using `generate_vat_payable_by_jurisdiction`.

## Example

```python
from vat_calculator import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00"},
    {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "4.00"},
    {"jurisdiction": "FR", "transaction_type": "sale", "amount": "100.00", "vat_rate": "0.20"},
]

result = generate_vat_payable_by_jurisdiction(transactions)
print(result["DE"]["vat_payable"])  # Decimal("15.00")
```

Each jurisdiction result includes:

- `output_vat`: total VAT collected on sales
- `input_vat`: total VAT paid on purchases
- `net_vat`: `output_vat - input_vat`
- `vat_payable`: positive net VAT (otherwise `0.00`)
- `vat_refundable`: negative net VAT as a positive value (otherwise `0.00`)
