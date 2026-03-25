# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction-level data.

## Input format

Provide a CSV file with the following columns:

- `jurisdiction` (required)
- `transaction_type` (required: `sale` or `purchase`)
- `net_amount` (required, decimal)
- `vat_rate` (required, decimal like `0.20` for 20%)
- `vat_amount` (optional; when blank it is calculated as `net_amount * vat_rate`)

## Usage

Install locally:

```bash
python -m pip install -e ".[dev]"
```

Run VAT payable generation:

```bash
vat-payable path/to/transactions.csv
```

Output columns:

- `jurisdiction`
- `output_vat`
- `input_vat`
- `vat_payable`
- `transaction_count`

`vat_payable` is calculated as:

```text
output_vat - input_vat
```
