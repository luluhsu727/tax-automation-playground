# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## VAT payable calculation

`vat_payable.py` aggregates VAT by `jurisdiction` and returns the net VAT amount:

- Positive amount: VAT payable to the tax authority
- Negative amount: VAT reclaimable

Supported transaction formats:

1. **Type-based VAT**

```json
{
  "jurisdiction": "DE",
  "transaction_type": "sale",
  "vat_amount": "120.00"
}
```

Rules:
- `sale`, `sales`, `output`, `invoice` -> `+vat_amount`
- `purchase`, `expense`, `input`, `bill` -> `-vat_amount`
- `adjustment`, `direct` (or missing `transaction_type`) -> signed `vat_amount` as provided

2. **Explicit VAT netting fields**

```json
{
  "jurisdiction": "GB",
  "vat_collected": "200.25",
  "vat_paid": "80.15"
}
```

Rule:
- Net effect = `vat_collected - vat_paid`

## Run

Create an input JSON file containing an array of transactions, then run:

```bash
python3 vat_payable.py --input transactions.json
```

Example output:

```json
{
  "DE": "89.50",
  "FR": "35.00"
}
```

## Tests

```bash
python3 -m pytest -q
```
