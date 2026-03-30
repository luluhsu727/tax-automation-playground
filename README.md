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

- `type` defaults to `sale` when omitted and can be `sale` or `purchase`.
- `vat_rate` accepts decimal fractions (for example, `0.20`) or percentages (`20`).
- If `vat_rate` is omitted, default rates are used for `DE`, `FR`, `ES`, and `IT`.

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

## Run tests

Install dev dependencies and run the test suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```
