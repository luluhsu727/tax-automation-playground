# tax-automation-playground

Generate VAT to be paid (or reclaimed) per jurisdiction from a list of VAT transactions.

## VAT payable by jurisdiction

Implemented in `vat.py`:

- `calculate_vat_payable_by_jurisdiction(transactions)`
- `generate_vat_payable_by_jurisdiction(transactions)` (alias)

### Transaction format

Each transaction is a mapping with:

- `jurisdiction` (string, required)
- `kind` (required):
  - output VAT: `sale`, `output`, `output_vat`, `collected_vat`
  - input VAT: `purchase`, `input`, `input_vat`, `paid_vat`
- and either:
  - `vat_amount`
  - or both `amount` and `vat_rate` (VAT = amount * vat_rate)

### Output

Returns a dictionary:

- key: jurisdiction
- value: net VAT as `Decimal`, rounded to 2 decimals
  - positive => VAT payable
  - negative => VAT reclaimable

### Example

```python
from vat import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "kind": "sale", "vat_amount": "190.00"},
    {"jurisdiction": "DE", "kind": "purchase", "vat_amount": "75.50"},
    {"jurisdiction": "FR", "kind": "output", "amount": "1000", "vat_rate": "0.20"},
    {"jurisdiction": "FR", "kind": "input", "amount": "200", "vat_rate": "0.20"},
]

result = calculate_vat_payable_by_jurisdiction(transactions)
# {'DE': Decimal('114.50'), 'FR': Decimal('160.00')}
```

## Run tests

```bash
python -m unittest -v
```
