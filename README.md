# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## Input format

Provide a JSON file containing a list of transactions:

```json
[
  {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
  {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20}
]
```

- `type` must be either `sale` or `purchase`.
- `vat_rate` is a decimal fraction (for example, `0.20` for 20%).

## Generate VAT payable report

```bash
python vat_payable.py transactions.json --output-csv vat_report.csv
```

This command:

1. Prints a JSON summary of VAT amounts grouped by jurisdiction.
2. Writes a CSV report with columns:
   `jurisdiction,output_vat,input_vat,vat_payable`.

`vat_payable` is calculated as:

`output_vat - input_vat`

where:
- `output_vat` is VAT collected on sales.
- `input_vat` is VAT paid on purchases.
