# tax-automation-playground

Generate VAT payable amounts per jurisdiction from transaction-level data.

## VAT payable calculator

Implemented in `vat_payable.py` with a primary API:

```python
from vat_payable import generate_vat_payable_by_jurisdiction
```

Each transaction should include:

- `jurisdiction` (string)
- `type` (`"sale"` or `"purchase"`)
- `amount` (taxable amount)
- `vat_rate` (e.g. `0.2` or `20`)
- optional `input_vat_recoverable` (purchase only, defaults to `True`)

### Example

```python
transactions = [
    {"jurisdiction": "UK", "type": "sale", "amount": 1000, "vat_rate": 0.2},
    {"jurisdiction": "UK", "type": "purchase", "amount": 200, "vat_rate": 20},
]
```

Run from CLI:

```bash
python3 vat_payable.py sample_transactions.json --pretty
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```
