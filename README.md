# tax-automation-playground

Generate VAT payable totals per jurisdiction.

## VAT payable by jurisdiction

`calculate_vat_payable_by_jurisdiction` computes:

`sum(output_vat) - sum(input_vat)` for each jurisdiction.

- Positive value: VAT payable
- Negative value: VAT recoverable

```python
from decimal import Decimal
from vat import VATRecord, calculate_vat_payable_by_jurisdiction

records = [
    VATRecord(jurisdiction="DE", output_vat=Decimal("120.00"), input_vat=Decimal("20.00")),
    VATRecord(jurisdiction="DE", output_vat=Decimal("80.00"), input_vat=Decimal("5.00")),
    VATRecord(jurisdiction="FR", output_vat=Decimal("50.00"), input_vat=Decimal("65.00")),
]

totals = calculate_vat_payable_by_jurisdiction(records)
# {"DE": Decimal("175.00"), "FR": Decimal("-15.00")}
```

You can also pass dictionaries and optionally clamp negative balances to zero:

```python
totals = calculate_vat_payable_by_jurisdiction(records, clamp_negative=True)
```
