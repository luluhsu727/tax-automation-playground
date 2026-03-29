# tax-automation-playground

Generate VAT to be paid for each jurisdiction based on transaction-level VAT.

## What this project does

Given transactions with:

- `jurisdiction` (for example `DE`, `FR`, `UK`)
- `vat_type` (`output` or `input`)
- `vat_amount`

the calculator produces totals per jurisdiction:

- `output_vat`
- `input_vat`
- `vat_payable` (`output_vat - input_vat`)

`vat_payable` can be negative when a jurisdiction has more recoverable input VAT than output VAT due.

## Quick usage

```python
from vat_calculator import calculate_vat_to_be_paid_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "vat_type": "output", "vat_amount": 120.50},
    {"jurisdiction": "DE", "vat_type": "input", "vat_amount": 20.50},
    {"jurisdiction": "FR", "vat_type": "output", "vat_amount": 50.00},
]

result = calculate_vat_to_be_paid_by_jurisdiction(transactions)
print(result)
```

Expected output:

```python
{
    "DE": {"output_vat": 120.5, "input_vat": 20.5, "vat_payable": 100.0},
    "FR": {"output_vat": 50.0, "input_vat": 0.0, "vat_payable": 50.0},
}
```

## Running tests

```bash
python -m unittest discover -s tests
```
