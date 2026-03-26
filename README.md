# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction or precomputed VAT data.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Input format

Provide a JSON array of records. Each record must contain `jurisdiction`, and can include:

- `output_vat` and `input_vat` directly, or
- `sales_amount` + `vat_rate`, and optionally `purchase_amount` + `deductible_vat_rate`

Rates accept either decimal fractions (`0.2`) or whole percentages (`20`).

Example `input.json`:

```json
[
  { "jurisdiction": "DE", "sales_amount": 1000, "vat_rate": 19, "purchase_amount": 200, "deductible_vat_rate": 19 },
  { "jurisdiction": "FR", "output_vat": 300, "input_vat": 80 },
  { "jurisdiction": "DE", "output_vat": 10, "input_vat": 2 }
]
```

## Generate VAT payable by jurisdiction

```bash
python3 -m src.vat_payable input.json
```

Example output:

```json
{
  "DE": 160.8,
  "FR": 220.0
}
```

Negative net VAT for a jurisdiction is treated as `0.0` payable.

## Run tests

```bash
python3 -m pytest
```
