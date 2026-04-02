# tax-automation-playground

Utilities for generating VAT to be paid for each jurisdiction.

## Usage

Prepare a JSON file containing transaction rows, for example:

```json
[
  {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
  {"jurisdiction": "DE", "type": "purchase", "amount": 250, "vat_rate": 0.19},
  {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20}
]
```

Then run:

```bash
python vat_payable.py transactions.json --output-csv vat_payable_by_jurisdiction.csv
```

This writes a jurisdiction summary CSV and prints a JSON breakdown with:

- `output_vat`
- `input_vat`
- `vat_payable`
