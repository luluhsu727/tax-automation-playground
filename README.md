# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## VAT payable logic

For each jurisdiction:

- **Output VAT** = sum of VAT on `sale` transactions
- **Input VAT** = sum of VAT on `purchase` transactions
- **VAT payable** = `output_vat - input_vat`

## Input CSV format

Required columns:

- `jurisdiction`
- `transaction_type` (`sale|sales|output|purchase|purchases|input|expense`)

One of the following must be provided:

- `vat_amount` (direct VAT amount), or
- both `net_amount` and `vat_rate` (VAT computed as `net_amount * vat_rate`)

Example:

```csv
jurisdiction,transaction_type,net_amount,vat_rate
DE,sale,100.00,0.19
DE,purchase,40.00,0.19
FR,sale,200.00,0.20
FR,purchase,75.00,0.20
```

## Run

```bash
python3 vat_payable.py --input transactions.csv --output vat_summary.csv
```

Output columns:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`

## Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
