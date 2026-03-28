# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## VAT payable utility

This repository provides a small Python utility to calculate:

- `output_vat` (VAT collected on sales)
- `input_vat` (VAT paid on purchases)
- `vat_payable` (`output_vat - input_vat`)

grouped by jurisdiction.

### Run with CSV input

```bash
python vat_payable.py transactions.csv --rate DE=0.19 --rate FR=0.20
```

Expected CSV columns:

- `jurisdiction` (required)
- `kind` (required, one of `sale`, `purchase`)
- either:
  - `vat_amount` (explicit VAT amount), or
  - `amount` + `vat_rate` (or fallback `--rate JURISDICTION=RATE`)

Example:

```csv
jurisdiction,kind,amount,vat_rate
DE,sale,1000,0.19
DE,purchase,100,0.19
FR,sale,500,0.20
FR,purchase,50,0.20
```

### Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
