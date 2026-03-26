# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction-level inputs.

## VAT payable rule

For each jurisdiction:

`vat_payable = output_vat (sales VAT) - input_vat (purchase VAT)`

## Input format

Transactions can include either:

- `vat_amount` directly, or
- `net_amount` + `vat_rate`

Required columns:

- `jurisdiction`
- `transaction_type` (`sale` or `purchase`)
- and either `vat_amount` OR (`net_amount` and `vat_rate`)

## CLI usage

```bash
python vat_payable.py input.csv -o vat_payable_by_jurisdiction.csv
```

The output CSV contains:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
