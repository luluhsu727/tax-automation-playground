# tax-automation-playground

Generate VAT to be paid for each jurisdiction from transaction data.

## Input CSV columns

The script expects:

- `transaction_id`
- `revenue`
- `vat_collected`
- either `jurisdiction` or `country` (ISO codes: `DE`, `FR`, `ES`, `IT`)

## Run

```bash
python3 vat_payable.py --input "/path/to/transactions.csv" --output "vat_payable_by_jurisdiction.csv"
```

## Output

`vat_payable_by_jurisdiction.csv` with:

- `jurisdiction`
- `total_revenue`
- `total_vat_collected`
- `total_expected_vat`
- `vat_to_be_paid` (`total_expected_vat - total_vat_collected`)
