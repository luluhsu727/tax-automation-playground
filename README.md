# tax-automation-playground

Generate VAT to be paid (or refunded) for each jurisdiction from transaction data.

## Input format

Provide a JSON file with either:

- an array of transactions, or
- an object containing a `transactions` array.

Each transaction supports:

- `jurisdiction` (string, required)
- `amount` (number, required, taxable base amount)
- `vat_rate` (number, required, can be `0.2` or `20` for 20%)
- `transaction_type` (string, required, `sale` or `purchase`)
- `deductible` (boolean, optional, purchases only; defaults to `true`)

## Run

```bash
python3 vat_payable.py path/to/transactions.json --pretty
```

## Output

For each jurisdiction:

- `output_vat`: VAT collected on sales
- `input_vat_credit`: deductible VAT on purchases
- `net_vat`: `output_vat - input_vat_credit`
- `vat_payable`: amount to pay (`max(net_vat, 0)`)
- `vat_refundable`: amount to reclaim (`max(-net_vat, 0)`)

## Test

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```
