# tax-automation-playground

Utilities for generating VAT to be paid for each jurisdiction.

## VAT calculation

The VAT position is calculated per jurisdiction:

- `output_vat`: VAT on sales
- `input_vat`: VAT on purchases
- `vat_payable`: `max(output_vat - input_vat, 0)`
- `vat_credit`: `max(input_vat - output_vat, 0)`

Use `generate_vat_to_be_paid_by_jurisdiction(...)` when you only need payable totals.

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
