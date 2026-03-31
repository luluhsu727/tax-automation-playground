# tax-automation-playground

Generate the VAT to be paid for each jurisdiction from a list of sales and purchase transactions.

## Quick start

```python
from vat_calculator import generate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
    {"jurisdiction": "DE", "type": "purchase", "amount": 200, "vat_rate": 0.19},
    {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
]

result = generate_vat_payable_by_jurisdiction(transactions)
print(result["DE"]["vat_payable"])  # Decimal('152.00')
print(result["FR"]["vat_payable"])  # Decimal('100.00')
```

## Transaction format

Each transaction is a mapping with:

- `jurisdiction` (str): country/region code or name.
- `type` (str): `"sale"` or `"purchase"`.
- `amount` (number): net amount (pre-VAT) when `vat_amount` is not supplied.
- `vat_rate` (number, optional): VAT rate as decimal (`0.2`) or percent (`20`).
- `vat_amount` (number, optional): explicit VAT amount. If supplied, it overrides `amount` + `vat_rate`.

## Output format

For each jurisdiction:

- `output_vat`: VAT charged on sales.
- `input_vat`: VAT paid on purchases.
- `net_vat`: `output_vat - input_vat`.
- `vat_payable`: amount to remit (`max(net_vat, 0)`).
- `vat_reclaimable`: recoverable credit (`max(-net_vat, 0)`).

All monetary values are returned as `Decimal` rounded to 2 decimal places.

## Run tests

```bash
python -m unittest discover -s tests
```
