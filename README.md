# tax-automation-playground

Generate VAT payable amounts for each jurisdiction from transaction data.

## VAT payable rule

For each jurisdiction:

`vat_payable = output_vat (sales VAT) - input_vat (purchase VAT)`

## Input format

Use a CSV file with columns:

- `jurisdiction`
- `transaction_type` (`sale` or `purchase`)
- Either:
  - `vat_amount`, or
  - `net_amount` + `vat_rate`

`vat_rate` supports decimal format (`0.19`) and whole-percent format (`19`).

## Run from CLI

```bash
python vat_payable.py transactions.csv -o vat_payable_by_jurisdiction.csv
```

The output CSV includes:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
