# tax-automation-playground

Generate VAT payable per jurisdiction from transaction data.

## JSON input flow (`vat_payable.py`)

Provide a JSON file containing a list of transactions:

```json
[
  {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
  {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20}
]
```

- `type` must be either `sale` or `purchase`.
- `vat_rate` may be a decimal fraction (`0.20`) or a percentage value (`20`).

Generate the VAT payable report:

```bash
python3 vat_payable.py transactions.json --output-csv vat_report.csv
```

This prints a JSON summary and writes a CSV with:
`jurisdiction,output_vat,input_vat,vat_payable`.

## CSV input flow (`jurisdiction_vat_payable.py`)

Provide a CSV with jurisdiction and taxable amount columns:

```csv
jurisdiction,taxable_amount,vat_rate
DE,1000,0.19
FR,500,0.20
```

Generate summary CSV:

```bash
python3 jurisdiction_vat_payable.py --input sample_transactions.csv --output vat_payable_by_jurisdiction.csv
```

## Run tests

```bash
python3 -m pytest -q
```
