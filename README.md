# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input shape

Use a JSON file containing either:

- an array of transaction objects, or
- an object with a top-level `transactions` array.

Each transaction supports:

- `jurisdiction` (string, required)
- `amount` (number, required)
- `vat_rate` (number, required unless `vat_collected` is provided)
  - decimal form (`0.2`) or percentage form (`20`)
- `vat_collected` (number, optional)
  - if omitted, computed as `amount * vat_rate`
- `vat_paid` (number, optional, defaults to `0`)

Per jurisdiction:

- `output_vat = sum(vat_collected)`
- `input_vat = sum(vat_paid)`
- `vat_payable = max(output_vat - input_vat, 0)`

## Run

```bash
python3 vat_payable.py transactions.json
```

## Test

```bash
python3 -m unittest -v
```
