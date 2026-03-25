# tax-automation-playground

Generate the VAT to be paid for each jurisdiction from a list of transactions.

## Transaction format

The calculator accepts a JSON list of transaction objects with:

- `jurisdiction`: country/region code, e.g. `"DE"`, `"FR"`.
- `type`: one of:
  - output VAT: `"sale"`, `"output"`, `"collected"`
  - input VAT: `"purchase"`, `"input"`, `"deductible"`
- VAT value fields:
  - either direct `vat_amount`
  - or `amount` + `vat_rate` (supports both `0.20` and `20` for 20%)

Example:

```json
[
  { "jurisdiction": "DE", "type": "sale", "vat_amount": "120.00" },
  { "jurisdiction": "DE", "type": "purchase", "vat_amount": "20.00" },
  { "jurisdiction": "FR", "type": "sale", "amount": "500", "vat_rate": "20" }
]
```

VAT payable is calculated per jurisdiction as:

`output VAT - input VAT`

## Run

```bash
python -m vat_payable.cli path/to/transactions.json
```

Example output:

```json
{
  "DE": "100.00",
  "FR": "100.00"
}
```

## Test

```bash
python -m pip install -e ".[dev]"
pytest -q
```
