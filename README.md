# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Usage

Prepare a JSON file containing a list of transactions.

Each transaction requires:
- `jurisdiction` (string)
- `type` (`sale`/`output` or `purchase`/`input`)
- either `vat_amount` OR both `amount` and `vat_rate`

Example:

```json
[
  {"jurisdiction": "DE", "type": "sale", "vat_amount": 120.0},
  {"jurisdiction": "DE", "type": "purchase", "vat_amount": 30.0},
  {"jurisdiction": "FR", "type": "sale", "amount": 200.0, "vat_rate": 0.2}
]
```

Run:

```bash
python vat_by_jurisdiction.py transactions.json
```

Output includes, per jurisdiction:
- `output_vat`
- `input_vat`
- `vat_payable` (non-negative)
- `vat_credit` (non-negative)

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
