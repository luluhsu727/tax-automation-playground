# tax-automation-playground

Generate the VAT position for each jurisdiction from transaction data.

## What it calculates

For each jurisdiction, the script returns:

- `output_vat`: VAT collected on sales/output transactions
- `input_vat`: VAT paid on purchases/input transactions
- `vat_payable`: `output_vat - input_vat`
- `position`:
  - `payable` when `vat_payable > 0`
  - `refund` when `vat_payable < 0`
  - `settled` when `vat_payable == 0`

## Supported transaction formats

1. Pre-computed output/input VAT:

```json
{ "jurisdiction": "DE", "output_vat": 100, "input_vat": 20 }
```

2. Single transaction with explicit VAT amount:

```json
{ "jurisdiction": "DE", "transaction_type": "sale", "vat_amount": 100 }
```

3. Single transaction with amount + VAT rate:

```json
{
  "jurisdiction": "DE",
  "transaction_type": "purchase",
  "amount": 200,
  "vat_rate": 0.2
}
```

`vat_rate` may be provided as `0.2` or `20` (percent).

For gross (VAT-inclusive) amounts, set:

```json
{ "is_vat_inclusive": true }
```

## Run

```bash
python vat_calculator.py transactions.json
```

## Test

```bash
python -m unittest -v
```
