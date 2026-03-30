# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Usage

Create an input JSON file with an array of transactions:

```json
[
  {
    "jurisdiction": "DE",
    "taxable_amount": 1000,
    "vat_rate": 0.19,
    "transaction_type": "sale"
  },
  {
    "jurisdiction": "DE",
    "taxable_amount": 500,
    "vat_rate": 0.19,
    "transaction_type": "purchase"
  }
]
```

Run:

```bash
python vat_payable.py input.json
```

Output format:

```json
{
  "DE": {
    "output_vat": 190.0,
    "input_vat": 95.0,
    "vat_to_be_paid": 95.0,
    "vat_credit": 0.0
  }
}
```

## Running tests

```bash
python -m unittest -v
```
