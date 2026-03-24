# tax-automation-playground

Generate VAT to be paid for each jurisdiction.

## Usage

```python
from vat_payable import generate_vat_to_be_paid_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "net_amount": "100", "vat_rate": "19"},
    {"jurisdiction": "DE", "vat_amount": "5.50"},
    {"jurisdiction": "FR", "net_amount": "100", "vat_rate": "20"},
]

result = generate_vat_to_be_paid_by_jurisdiction(transactions)
# {"DE": Decimal("24.50"), "FR": Decimal("20.00")}
```

Input rows can provide either:
- `vat_amount` directly, or
- `net_amount` + `vat_rate` (rate can be decimal like `0.2` or percentage like `20`).

## Run tests

```bash
python -m unittest discover -s tests -v
```
