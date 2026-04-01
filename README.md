# tax-automation-playground

Generate VAT payable totals for each jurisdiction from transaction data.

## Input format

Provide JSON as either:

- an array of transactions, or
- an object with a `transactions` array.

Each transaction must include:

- `jurisdiction` (string)
- either `vat_amount`
- or both `taxable_amount` and `vat_rate`

`vat_rate` accepts decimal form (`0.2`) or percentage form (`20`).

## Usage

From stdin:

```bash
echo '[{"jurisdiction":"DE","taxable_amount":"100","vat_rate":"0.19"}]' | python3 vat_payable.py
```

From file:

```bash
python3 vat_payable.py input.json
```

## Run tests

```bash
python3 -m unittest discover -s tests
```
