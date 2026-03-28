# tax-automation-playground

Generate VAT to be paid for each jurisdiction from VAT-relevant transactions.

## What this provides

- A reusable function:
  - `generate_vat_payable_by_jurisdiction(records)`
- A CLI command:
  - `python -m vat_automation.cli <transactions.json|transactions.csv>`

VAT payable is calculated as:

- `sale` VAT: increases liability
- `purchase` VAT: decreases liability (input tax credit)
- Net payable per jurisdiction is clamped at `0.00` (no negative payable)

## Transaction input format

Each transaction requires:

- `jurisdiction` (string)
- `kind` (`sale` or `purchase`)
- and either:
  - `vat_amount`
  - or `amount` + `vat_rate` (where VAT = amount * vat_rate)

### JSON example

```json
[
  {"jurisdiction": "DE", "kind": "sale", "amount": "100.00", "vat_rate": "0.19"},
  {"jurisdiction": "DE", "kind": "purchase", "amount": "10.00", "vat_rate": "0.19"},
  {"jurisdiction": "FR", "kind": "sale", "vat_amount": "8.50"}
]
```

### CSV example

```csv
jurisdiction,kind,amount,vat_rate,vat_amount
DE,sale,100.00,0.19,
DE,purchase,10.00,0.19,
FR,sale,,,8.50
```

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m vat_automation.cli transactions.json --pretty
```

Example output:

```json
{
  "DE": "17.10",
  "FR": "8.50"
}
```

## Tests

```bash
pytest
```
