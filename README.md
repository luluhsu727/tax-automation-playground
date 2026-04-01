# tax-automation-playground

Generate VAT payable per jurisdiction from transaction-level data.

## What this does

The calculator groups transactions by jurisdiction and computes:

- `output_vat`: VAT collected on sales
- `input_vat`: VAT paid on purchases
- `vat_payable`: `output_vat - input_vat`

Positive `vat_payable` means VAT to be paid. Negative means VAT refundable/credit.

## Transaction format

Each transaction needs:

- `jurisdiction`: string (for example `DE`, `FR`)
- `amount`: net amount (before VAT)
- `vat_rate`: VAT rate as decimal (`0.20`) or percentage (`20`)
- `transaction_type`: `sale` or `purchase`
- `vat_amount` (optional): explicit VAT value, overrides `amount * vat_rate`

## CLI usage

Use CSV input to generate a jurisdiction VAT report:

```bash
python -m vat_payable --input transactions.csv
```

Optional JSON output:

```bash
python -m vat_payable --input transactions.csv --format json
```

CSV header example:

```csv
jurisdiction,amount,vat_rate,transaction_type,vat_amount
DE,1000,19,sale,
DE,200,19,purchase,
FR,800,20,sale,160
```
