# tax-automation-playground

## VAT payable by jurisdiction

This repository includes a small utility to generate VAT to be paid for each
jurisdiction based on transaction-level VAT records.

### Input format

Provide a JSON array where each object includes:

- `jurisdiction` (string)
- `output_vat` (number or numeric string): VAT charged on sales
- `input_vat` (number or numeric string): VAT paid on purchases

Example:

```json
[
  {"jurisdiction": "DE", "output_vat": "100.00", "input_vat": "20.00"},
  {"jurisdiction": "DE", "output_vat": "10.25", "input_vat": "2.15"},
  {"jurisdiction": "FR", "output_vat": "50.00", "input_vat": "70.00"}
]
```

### Run

```bash
python vat_payable.py --input records.json --pretty
```

### Output

Output is grouped by jurisdiction and includes:

- `output_vat`: summed output VAT
- `input_vat`: summed input VAT
- `vat_payable`: `output_vat - input_vat`

Example output:

```json
{
  "DE": {
    "input_vat": "22.15",
    "output_vat": "110.25",
    "vat_payable": "88.10"
  },
  "FR": {
    "input_vat": "70.00",
    "output_vat": "50.00",
    "vat_payable": "-20.00"
  }
}
```

### Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
