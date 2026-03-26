# tax-automation-playground

Generate VAT payable per jurisdiction from transaction-level CSV data.

## Input format

Input CSV must include:

- `jurisdiction` (e.g. `DE`, `FR`, `UK`)
- `transaction_type` (`sale` or `purchase`)
- `net_amount` (numeric)
- `vat_rate` (decimal VAT rate, e.g. `0.20` for 20%)

## VAT payable logic

For each jurisdiction:

- Output VAT = sum of `net_amount * vat_rate` for `sale` rows
- Input VAT = sum of `net_amount * vat_rate` for `purchase` rows
- VAT payable = Output VAT - Input VAT

All VAT monetary values are rounded to 2 decimal places with half-up rounding.

## Run

```bash
python -m tax.cli --input transactions.csv --output vat_payable.csv
```
