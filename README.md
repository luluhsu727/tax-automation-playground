# tax-automation-playground

Generate VAT payable for each jurisdiction from transaction data.

## Usage

Create a JSON file with an array of transactions. Each transaction must include:

- `jurisdiction` (string)
- `transaction_type` (either `sale` or `purchase`; `type` is also accepted)
- Either:
  - `vat_amount`
  - or both `net_amount` and `vat_rate` (rate can be decimal like `0.2` or percentage like `20`)

### Example input (`transactions.json`)

```json
[
  {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": 10.0},
  {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": 2.5},
  {"jurisdiction": "FR", "transaction_type": "sale", "net_amount": 100, "vat_rate": 20}
]
```

### Run

```bash
python vat_payable.py transactions.json
```

Example output:

```text
DE: 7.50
FR: 20.00
```

JSON output:

```bash
python vat_payable.py transactions.json --json
```
