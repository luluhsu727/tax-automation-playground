# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Usage

```bash
python jurisdiction_vat_payable.py --input transactions.csv --output vat_payable_by_jurisdiction.csv
```

Supported inputs:

- CSV with columns including:
  - jurisdiction or country
  - taxable_amount, net_amount, revenue, or amount
  - optional vat_rate/rate
  - optional transaction_type/type (`sale` or `purchase`)
- JSON array of transaction objects with equivalent keys

## Programmatic API

- `generate_vat_to_be_paid_for_each_jurisdiction(transactions)` -> `dict[jurisdiction, Decimal]`
- `compute_vat_payable_by_jurisdiction(transactions)` -> jurisdiction summary rows
- `calculate_vat_payable_by_jurisdiction(transactions)` -> output/input/net VAT amounts
