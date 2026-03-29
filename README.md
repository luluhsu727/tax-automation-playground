# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## What this implementation does

The VAT engine computes, for each jurisdiction:

- **output_vat**: VAT collected on `sale` transactions
- **input_vat**: VAT paid on `purchase` transactions
- **vat_payable**: `output_vat - input_vat`

## Input transaction schema

Each transaction record requires:

- `jurisdiction` (string)
- `transaction_type` (`sale` or `purchase`)
- either:
  - `vat_amount`, or
  - both `taxable_amount` and `vat_rate`

`vat_rate` accepts either decimal form (`0.2`) or percent form (`20`).

## Usage (CLI)

```bash
python3 vat_payable.py transactions.csv --output-csv vat_payable_report.csv
```

Input CSV headers:

```text
jurisdiction,transaction_type,taxable_amount,vat_rate,vat_amount
```

The output CSV will contain:

```text
jurisdiction,output_vat,input_vat,vat_payable
```

## Run tests

```bash
python3 -m unittest -v
```
