# tax-automation-playground

## Generate VAT to be paid for each jurisdiction

This repository includes a small utility that computes VAT payable totals per jurisdiction.

### Run from Python

```python
from jurisdiction_vat_payable import generate_vat_to_be_paid_for_each_jurisdiction

transactions = [
    {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": None},
    {"jurisdiction": "FR", "taxable_amount": "200.00", "vat_rate": "0.20"},
]

result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
# {"DE": Decimal("19.00"), "FR": Decimal("40.00")}
```

### Run from CSV

```bash
python jurisdiction_vat_payable.py --input sample_transactions.csv --output vat_payable_by_jurisdiction.csv
```

Input CSV columns supported:

- Jurisdiction: `jurisdiction` or `country`
- Taxable amount: `taxable_amount`, `net_amount`, `revenue`, or `amount`
- VAT rate (optional): `vat_rate` or `rate`

If VAT rate is omitted in rows, built-in defaults are used for `DE`, `FR`, `ES`, and `IT`.
