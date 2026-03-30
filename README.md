# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## VAT payable generator

The script `vat_payable.py` calculates, for each jurisdiction:

- `output_vat`: VAT collected from sales transactions
- `input_vat`: VAT paid on purchases/expenses
- `vat_payable`: `output_vat - input_vat`
- `status`:
  - `payable` when net VAT is positive
  - `refundable` when net VAT is negative
  - `balanced` when net VAT is zero

### Input CSV format

Required columns:

- `jurisdiction`
- one of `transaction_type` or `type` (`sale`/`sales`/`output` or `purchase`/`purchases`/`expense`/`input`)
- either:
  - `vat_amount`, or
  - both `amount` and `vat_rate` (`vat_rate` can be `0.2` or `20`)

Example:

```csv
jurisdiction,transaction_type,amount,vat_rate
DE,sale,100,0.19
DE,purchase,50,0.19
FR,sale,200,20
FR,purchase,100,20
```

### Run

Print summary CSV to stdout:

```bash
python vat_payable.py transactions.csv
```

Write summary CSV to a file:

```bash
python vat_payable.py transactions.csv --output-csv vat_summary.csv
```

### Tests

```bash
python -m unittest -v
```
