# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## VAT payable rule

For each jurisdiction:

`vat_payable = output_vat (sales VAT) - input_vat (purchase VAT)`

## Input format

Use a CSV with these columns:

- `jurisdiction`
- `transaction_type` (`sale` or `purchase`)
- Either:
  - `vat_amount`, or
  - `net_amount` + `vat_rate`

`vat_rate` supports either decimal format (`0.19`) or whole-percent (`19`).

## Run from CLI

```bash
python vat_payable.py transactions.csv -o vat_payable_by_jurisdiction.csv
```

This writes a jurisdiction summary CSV with:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
