# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction-level data.

## VAT payable model

For each jurisdiction:

- `output_vat` = sum of VAT on sales
- `input_vat` = sum of VAT on purchases
- `vat_payable` = `output_vat - input_vat`

If `vat_payable` is negative, it indicates a potential refundable VAT position.

## Input format

Pass a JSON array of transactions. Each item requires:

- `jurisdiction`: string (e.g. `DE`, `FR`)
- `transaction_type`: `sale` or `purchase`

VAT can be provided either as:

- `vat_amount` (direct), or
- `net_amount` and `vat_rate` (computed as `net_amount * vat_rate`)

## Run

```bash
python vat_payable.py transactions.json
```

## Test

```bash
pytest -q
```
