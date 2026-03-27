# tax-automation-playground

Generate the VAT to be paid for each jurisdiction from a list of transactions.

## VAT payable by jurisdiction

Use `generate_vat_payable_by_jurisdiction` from `vat_payable.py`:

```python
from vat_payable import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19", "transaction_type": "sale"},
    {"jurisdiction": "DE", "amount": "20.00", "vat_rate": "0.19", "transaction_type": "purchase"},
    {"jurisdiction": "FR", "amount": "80.00", "vat_rate": "0.20", "transaction_type": "sale"},
]

totals = generate_vat_payable_by_jurisdiction(transactions)
```

The function returns one entry per jurisdiction with:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `net_vat`: `output_vat - input_vat`
- `vat_payable`: `max(net_vat, 0)`
- `vat_refundable`: `max(-net_vat, 0)`

## Run tests

```bash
python -m unittest -v
```
