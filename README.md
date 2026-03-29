# tax-automation-playground

Generate the VAT to be paid for each jurisdiction from transaction data.

## Run from CSV

```bash
python3 jurisdiction_vat_payable.py \
  --input sample_transactions.csv \
  --output vat_payable_by_jurisdiction.csv
```

Input CSV must include:

- a jurisdiction column (`jurisdiction` or `country`)
- a taxable amount column (`taxable_amount`, `net_amount`, `revenue`, or `amount`)
- optionally, a VAT rate column (`vat_rate` or `rate`)

If no row-level VAT rate is provided, default rates are used for:

- DE: `0.19`
- FR: `0.20`
- ES: `0.21`
- IT: `0.22`

## Programmatic usage

```python
from jurisdiction_vat_payable import generate_vat_to_be_paid_for_each_jurisdiction

transactions = [
    {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": "0.19"},
    {"jurisdiction": "FR", "taxable_amount": "80.00", "vat_rate": "0.20"},
]

vat_to_be_paid = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
# {"DE": Decimal("19.00"), "FR": Decimal("16.00")}
```
