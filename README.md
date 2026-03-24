# tax-automation-playground

Generate VAT totals and VAT payable per jurisdiction from transaction CSV data.

## Input format

The input CSV must include:

- `transaction_id`
- `revenue`
- `vat_collected`
- either `jurisdiction` or `country` (ISO code like `DE`, `FR`, `ES`, `IT`)

## Run

```bash
python3 vat_check.py \
  --input "/path/to/transactions.csv" \
  --output "vat_check_results.csv" \
  --summary-output "vat_payable_by_jurisdiction.csv"
```

## Output files

- `vat_check_results.csv`: transaction-level VAT calculations with `vat_payable`
- `vat_payable_by_jurisdiction.csv`: summary table with one row per jurisdiction and
  `vat_payable` equal to `total_expected_vat - total_vat_collected`
