# tax-automation-playground

Generate VAT payable totals for each jurisdiction.

## VAT payable by jurisdiction

VAT payable is calculated per transaction as:

`output_vat - input_vat`

Then values are aggregated by jurisdiction.

### Input format

Provide a JSON array of transaction objects, for example:

```json
[
  { "jurisdiction": "DE", "output_vat": "120.10", "input_vat": "20.10" },
  { "jurisdiction": "DE", "output_vat": 30, "input_vat": 10 },
  { "jurisdiction": "FR", "output_vat": "55.50", "input_vat": "60.00" }
]
```

### Run

```bash
python vat_payable.py --input transactions.json
```

Example output:

```json
{
  "DE": "120.00",
  "FR": "-4.50"
}
```

### Tests

```bash
python -m unittest discover -s tests -v
```
