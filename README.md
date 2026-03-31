# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Transaction model

Each transaction is a JSON object with:

- `jurisdiction` (string, required): e.g. `DE`, `FR`
- `transaction_type` (required): `"sale"` or `"purchase"`
- Either:
  - `vat_amount` (number-like), or
  - `net_amount` and `vat_rate` (where VAT = `net_amount * vat_rate`)

Computation rules:

- Sales contribute to **output VAT**
- Purchases contribute to **input VAT**
- **VAT to be paid** = `output_vat - input_vat`
- Values are rounded to 2 decimals using half-up rounding.

## Usage

Create an input JSON file with an array of transactions, for example:

```json
[
  { "jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00" },
  { "jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "4.00" },
  { "jurisdiction": "FR", "transaction_type": "sale", "net_amount": "100.00", "vat_rate": "0.20" }
]
```

Run:

```bash
python3 vat_payable.py transactions.json
```

Output format:

```text
jurisdiction,output_vat,input_vat,vat_to_be_paid
DE,19.00,4.00,15.00
FR,20.00,0.00,20.00
```

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
