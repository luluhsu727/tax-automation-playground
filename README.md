# tax-automation-playground

Generate VAT to be paid for each jurisdiction from JSON records.

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

## CLI usage

Create an input JSON file containing an array of records:

```json
[
  {"jurisdiction": "DE", "output_vat": 120, "input_vat": 20},
  {
    "jurisdiction": "FR",
    "sales_amount": 1000,
    "vat_rate": 20,
    "purchase_amount": 100,
    "deductible_vat_rate": 20
  }
]
```

Then run:

```bash
python3 -m src.vat_payable records.json
```

Output is JSON mapping each jurisdiction to VAT payable (never negative).
