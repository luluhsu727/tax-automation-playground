# tax-automation-playground

Compute VAT to be paid per jurisdiction from transaction-level data.

## VAT payable definition

For each jurisdiction:

- **output VAT** = VAT collected on `sale` transactions
- **input VAT** = VAT paid on `purchase` transactions
- **vat payable** = `output VAT - input VAT`

## Input format

Provide a JSON array where each item includes:

- `jurisdiction` (string)
- `net_amount` (number/string decimal)
- `vat_rate` (number/string decimal, e.g. `0.20` for 20%)
- `transaction_type` (`sale` or `purchase`)
- optional `vat_amount` (number/string decimal) to override `net_amount * vat_rate`

## Run

```bash
python3 vat_payable.py --input transactions.json
```

## Test

```bash
python3 -m unittest -v
```
