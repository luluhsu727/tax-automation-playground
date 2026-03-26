# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## VAT payable logic

For each jurisdiction:

- output VAT = sum of VAT from `sale` transactions
- input VAT = sum of VAT from `purchase` transactions
- VAT payable = output VAT - input VAT

Each transaction can provide:

- `vat_amount` directly, or
- `net_amount` and `vat_rate` (VAT is calculated as `net_amount * vat_rate`)

## Usage

Input CSV columns:

- `jurisdiction`
- `transaction_type` (`sale` or `purchase`)
- `vat_amount` (optional if `net_amount` and `vat_rate` are provided)
- `net_amount` (optional)
- `vat_rate` (optional)

Run:

```bash
python vat_payable.py path/to/transactions.csv
```

JSON output:

```bash
python vat_payable.py path/to/transactions.csv --json
```

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
