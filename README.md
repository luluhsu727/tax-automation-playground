# tax-automation-playground

Generate VAT payable amounts per jurisdiction.

## What is VAT payable?

For each jurisdiction:

`VAT payable = output VAT (sales) - input VAT (purchases)`

Positive values indicate VAT owed to the tax authority. Negative values indicate
recoverable VAT (credit).

## Data format

The calculator accepts a list of transactions. Each transaction includes:

- `jurisdiction` (string, required)
- `transaction_type` (string, required): one of `sale`, `output`, `purchase`,
  `input`
- `vat_amount` (number/string, optional): VAT amount directly
- `net_amount` (number/string, optional): taxable amount before VAT
- `vat_rate` (number/string, optional): VAT rate (for example `0.2` for 20%)

If `vat_amount` is provided, it is used as-is. Otherwise, the calculator
computes VAT as `net_amount * vat_rate`.

## CLI usage

Create an input file:

```json
[
  {
    "jurisdiction": "DE",
    "transaction_type": "sale",
    "net_amount": "100.00",
    "vat_rate": "0.19"
  },
  {
    "jurisdiction": "DE",
    "transaction_type": "purchase",
    "net_amount": "20.00",
    "vat_rate": "0.19"
  }
]
```

Run:

```bash
python vat_calculator.py transactions.json
```

Output:

```json
{
  "DE": "15.20"
}
```

## Tests

```bash
python -m unittest discover -s tests -v
```
