# tax-automation-playground

Generate the VAT to be paid for each jurisdiction with `jurisdiction_vat_payable.py`.

## Usage

Create an input CSV with at least:

- a jurisdiction column (`jurisdiction` or `country`)
- a taxable amount column (`taxable_amount`, `net_amount`, `revenue`, or `amount`)
- optional VAT rate column (`vat_rate` or `rate`)

Then run:

```bash
python3 jurisdiction_vat_payable.py --input sample_transactions.csv --output vat_payable_by_jurisdiction.csv
```

The output file includes:

- `jurisdiction`
- `total_taxable_amount`
- `total_vat_payable`
- `effective_vat_rate`

## Running tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
