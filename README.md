# tax-automation-playground

Generate VAT payable totals for each jurisdiction from transaction-level data.

## VAT payable by jurisdiction

`vat_payable.py` calculates:

- **output VAT** for sale transactions
- **input VAT** for purchase transactions
- **VAT payable** per jurisdiction as:
  - `vat_payable = output_vat - input_vat`

If a value is positive, VAT is payable to tax authorities; if negative, it is in a reclaim/refund position.

### Input CSV columns

Required columns:

- `jurisdiction`
- `transaction_type` (`sale`/`output` or `purchase`/`input`)
- `net_amount`

Optional columns (at least one of these must be present per row):

- `vat_rate` (e.g. `0.19`)
- `vat_amount` (explicit VAT amount)

### Run

```bash
python3 vat_payable.py --input sample_transactions.csv --output vat_payable_by_jurisdiction.csv
```

### Test

```bash
python3 -m pytest -q
```
