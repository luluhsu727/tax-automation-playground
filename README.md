# tax-automation-playground

Generate VAT payable by jurisdiction from transaction data.

## Input format

Provide a CSV with these columns:

- `jurisdiction` (example: `DE`, `FR`)
- `transaction_type` (`sale` or `purchase`)
- `net_amount` (decimal)
- `vat_rate` (decimal, e.g. `0.19` for 19%)

Example:

```csv
jurisdiction,transaction_type,net_amount,vat_rate
DE,sale,100.00,0.19
DE,purchase,40.00,0.19
FR,sale,100.00,0.20
FR,purchase,150.00,0.20
```

## Usage

```bash
python vat_payable.py --input input.csv --output output.csv
```

The output includes, for each jurisdiction:

- `output_vat`
- `input_vat`
- `net_vat` (`output_vat - input_vat`)
- `payable_vat` (max of `net_vat` and `0`)
- `refundable_vat` (max of `-net_vat` and `0`)

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
