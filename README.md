# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## What this computes

For each jurisdiction:

- `output_vat`: VAT from `sale` transactions
- `input_vat`: VAT from `purchase` transactions
- `vat_to_be_paid`: `output_vat - input_vat`

## Transaction format

Each transaction is a dictionary with:

- `jurisdiction` (string)
- `transaction_type` (`"sale"` or `"purchase"`)  
  - alias supported: `type`
- `net_amount` (numeric)  
  - alias supported: `amount`
- `vat_rate` (decimal between `0` and `1`)

## Example

```python
from vat_calculator import calculate_vat_to_be_paid

transactions = [
    {"jurisdiction": "DE", "transaction_type": "sale", "net_amount": 100, "vat_rate": 0.19},
    {"jurisdiction": "DE", "transaction_type": "purchase", "net_amount": 20, "vat_rate": 0.19},
    {"jurisdiction": "FR", "transaction_type": "sale", "net_amount": 200, "vat_rate": 0.20},
]

result = calculate_vat_to_be_paid(transactions)
print(result)
```

Example output:

```python
{
    "DE": {
        "output_vat": Decimal("19.00"),
        "input_vat": Decimal("3.80"),
        "vat_to_be_paid": Decimal("15.20"),
    },
    "FR": {
        "output_vat": Decimal("40.00"),
        "input_vat": Decimal("0.00"),
        "vat_to_be_paid": Decimal("40.00"),
    },
}
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```
