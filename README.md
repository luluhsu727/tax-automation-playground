# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction-level VAT records.

## Input format

Provide a CSV file with these required columns:

- `jurisdiction` (for example: `DE`, `FR`, `UK`)
- `tax_direction` (`output`/`sale`/`sales`/`collected` for output VAT, `input`/`purchase`/`purchases`/`deductible` for input VAT)
- `vat_amount` (decimal number)

Example:

```csv
jurisdiction,tax_direction,vat_amount
DE,sale,120.00
DE,purchase,20.00
FR,output,55.50
FR,input,60.50
```

## Generate VAT payable summary

```bash
python vat_payable.py transactions.csv --output-csv vat_payable_by_jurisdiction.csv
```

The output CSV contains:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `net_vat` (`output_vat - input_vat`)
- `vat_to_be_paid` (`max(net_vat, 0)`)
- `vat_credit` (`max(-net_vat, 0)`)

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
