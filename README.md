# tax-automation-playground

Generate the VAT payable for each jurisdiction from transaction data.

## Input shape

Provide a JSON array where each object includes:

- `jurisdiction` (string)
- `transaction_type` (`sale`/`output` or `purchase`/`input`)
- Either:
  - `vat_amount`
  - OR `net_amount` + `vat_rate` (accepts `0.2` or `20`)

Example:

```json
[
  { "jurisdiction": "DE", "transaction_type": "sale", "net_amount": 1000, "vat_rate": 0.19 },
  { "jurisdiction": "DE", "transaction_type": "purchase", "net_amount": 300, "vat_rate": 0.19 },
  { "jurisdiction": "FR", "transaction_type": "sale", "vat_amount": 200 },
  { "jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": 250 }
]
```

## Run

```bash
python3 scripts/calculate_vat_payable.py sample_transactions.json
```

Expected output (formatted):

```json
{
  "DE": {
    "input_vat": "57.00",
    "net_vat": "133.00",
    "output_vat": "190.00",
    "vat_payable": "133.00"
  },
  "FR": {
    "input_vat": "250.00",
    "net_vat": "-50.00",
    "output_vat": "200.00",
    "vat_payable": "0.00"
  }
}
```

`vat_payable` is clamped at `0.00` when net VAT is negative.

## Test

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```
