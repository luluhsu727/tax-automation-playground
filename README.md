# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction records.

## VAT payable by jurisdiction

The `calculate_vat_to_be_paid_by_jurisdiction` helper aggregates VAT across
records and returns, per jurisdiction:

- `output_vat` (VAT from sales)
- `input_vat` (VAT from purchases)
- `net_vat` (`output_vat - input_vat`)
- `vat_to_be_paid` (`max(net_vat, 0)`)
- `refund_due` (`max(-net_vat, 0)`)
- `status` (`payable` or `refund_or_zero`)

## Usage

```python
from vat_payable import calculate_vat_to_be_paid_by_jurisdiction

records = [
    {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "120.00"},
    {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "20.00"},
    {"jurisdiction": "FR", "transaction_type": "sale", "taxable_amount": "100.00", "vat_rate": "0.20"},
]

result = calculate_vat_to_be_paid_by_jurisdiction(records)
print(result["DE"]["vat_to_be_paid"])  # Decimal("100.00")
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
