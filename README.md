# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Transaction format

Each transaction must include:

- `jurisdiction`: jurisdiction code/name (for example: `DE`, `FR`)
- `transaction_type`: `sale` or `purchase`
- Either:
  - `vat_amount`
  - or both `amount` and `vat_rate`

`vat_rate` can be supplied as either a decimal (for example `0.2`) or percentage
(for example `20`).

## Run

```bash
python main.py transactions.json
```

The output is JSON with VAT figures per jurisdiction including:

- `output_vat`
- `input_vat`
- `net_vat`
- `payable_vat`
- `reclaimable_vat`

`payable_vat` is the VAT to be paid for each jurisdiction.

## Test

```bash
python -m unittest -v
```
