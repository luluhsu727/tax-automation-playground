# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Transaction model

Each transaction requires:

- `jurisdiction`: string identifier such as `DE`, `FR`, `UK`, `CA-ON`
- `net_amount`: amount excluding VAT
- `vat_rate`: decimal VAT rate (for example `0.20` for 20%)
- `transaction_type`: `sale` or `purchase`

VAT payable is calculated as:

`sum(sale VAT) - sum(purchase VAT)` grouped by jurisdiction.

## Python API

```python
from src.vat_payable import generate_vat_payable_report

transactions = [
    {"jurisdiction": "DE", "net_amount": "100.00", "vat_rate": "0.19", "transaction_type": "sale"},
    {"jurisdiction": "DE", "net_amount": "50.00", "vat_rate": "0.19", "transaction_type": "purchase"},
    {"jurisdiction": "FR", "net_amount": "200.00", "vat_rate": "0.20", "transaction_type": "sale"},
]

print(generate_vat_payable_report(transactions))
# {"DE": "9.50", "FR": "40.00"}
```

## CLI

Pass JSON list input through stdin:

```bash
python -m src.vat_payable --input - <<'JSON'
[
  {"jurisdiction":"DE","net_amount":"100.00","vat_rate":"0.19","transaction_type":"sale"},
  {"jurisdiction":"DE","net_amount":"50.00","vat_rate":"0.19","transaction_type":"purchase"},
  {"jurisdiction":"FR","net_amount":"200.00","vat_rate":"0.20","transaction_type":"sale"}
]
JSON
```

Output:

```json
{"DE":"9.50","FR":"40.00"}
```
