# tax-automation-playground

Generate VAT to be paid for each jurisdiction.

## What this repository now provides

- `vat.py` with reusable functions to calculate VAT balances.
- Per-jurisdiction net VAT (output VAT - recoverable input VAT).
- A convenience function that returns **VAT payable only** (credits clamped to `0`).

## Transaction shape

Each transaction is a mapping with:

- `jurisdiction` (required): country/region code (e.g. `DE`, `FR`).
- `type` or `direction` (required): `sale`/`output` or `purchase`/`input`.
- Either:
  - `vat_amount` (explicit VAT amount), or
  - both `amount` and `vat_rate` (VAT will be computed).
- `recoverable` (optional, purchase only): defaults to `True`.

## Example

```python
from vat import generate_vat_payable_for_each_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
    {"jurisdiction": "DE", "type": "purchase", "amount": 300, "vat_rate": 0.19},
    {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
    {"jurisdiction": "FR", "type": "purchase", "amount": 700, "vat_rate": 0.20},
]

vat_payable = generate_vat_payable_for_each_jurisdiction(transactions)
print(vat_payable)
# {'DE': Decimal('133.00'), 'FR': Decimal('0.00')}
```

## Run tests

```bash
python -m unittest -v
```
