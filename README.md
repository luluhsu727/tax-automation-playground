# tax-automation-playground

Generate VAT payable for each jurisdiction.

## VAT payable definition

For each jurisdiction:

`vat_payable = output_vat_on_sales - input_vat_on_purchases`

## Python API

```python
from vat_payable import calculate_vat_payable_by_jurisdiction

transactions = [
    {"jurisdiction": "DE", "type": "sale", "vat": "120.50"},
    {"jurisdiction": "DE", "type": "purchase", "vat": "20.25"},
    {"jurisdiction": "FR", "type": "sale", "vat": "80"},
]

result = calculate_vat_payable_by_jurisdiction(transactions)
# {"DE": Decimal("100.25"), "FR": Decimal("80")}
```

## CLI usage

Input can be either:

- A JSON array of transactions, or
- A JSON object with a `transactions` array

Each transaction must contain:

- `jurisdiction` (string)
- `type` (`"sale"` or `"purchase"`)
- `vat` (number-like)

### Example

```bash
python vat_payable_cli.py --pretty -i sample_transactions.json
```

Output:

```json
{
  "vat_payable_by_jurisdiction": {
    "DE": "100.25",
    "FR": "80"
  }
}
```
