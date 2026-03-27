# tax-automation-playground

Utilities to generate VAT to be paid for each jurisdiction.

## Primary entrypoints

- `vat_calculator.py`
  - `generate_vat_to_be_paid_by_jurisdiction(transactions)`
  - `generate_vat_to_be_paid_for_each_jurisdiction(transactions)` (alias)
- `jurisdiction_vat_payable.py`
  - CSV loader and CSV summary writer for jurisdiction VAT payable
- `vat_payable` package
  - calculator + CLI: `python3 -m vat_payable.cli <transactions.json>`
- `vat_check.py`
  - reconciliation-style CSV processor generating transaction + summary outputs

## Run tests

```bash
python3 -m pytest -q
```
