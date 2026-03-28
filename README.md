# tax-automation-playground

Generate VAT totals and VAT payable per jurisdiction from CSV transaction data.

## What it calculates

For each jurisdiction, the script calculates:

- `output_vat` (VAT collected on sales)
- `input_vat` (deductible VAT on purchases)
- `net_vat` (`output_vat - input_vat`)
- `vat_to_be_paid` (`max(net_vat, 0)`)
- `vat_credit_carry_forward` (`max(-net_vat, 0)`)

## Usage

```bash
python3 vat_payable.py path/to/transactions.csv -o vat_payable_by_jurisdiction.csv
```

## Accepted input column formats

Each row must contain a jurisdiction column (`jurisdiction`, `country`, or `region`) and one of these VAT input styles:

1. Explicit output/input VAT fields:
   - Output: `vat_collected`, `output_vat`, `sales_vat`, `vat_output`
   - Input: `vat_deductible`, `input_vat`, `purchase_vat`, `vat_input`

2. VAT amount + type:
   - Amount: `vat_amount`
   - Type: `vat_type` (or `transaction_type` / `type`) with values like `output` or `input`

3. Taxable amount + VAT rate + type:
   - Amount: `taxable_amount` (or `net_amount` / `amount_ex_vat` / `amount`)
   - Rate: `vat_rate` (or `tax_rate` / `rate`), accepts both `21` and `0.21`
   - Type: `vat_type` (or `transaction_type` / `type`)

## Run tests

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
