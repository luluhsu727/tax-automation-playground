# tax-automation-playground

Generate VAT payable per jurisdiction from VAT movements.

## Usage

```python
from vat import VATEntry, generate_vat_payable_by_jurisdiction

entries = [
    VATEntry(jurisdiction="DE", output_vat="100.00", input_vat="35.00"),
    VATEntry(jurisdiction="DE", output_vat="20.00", input_vat="10.00"),
    VATEntry(jurisdiction="FR", output_vat="50.00", input_vat="65.00"),
]

results = generate_vat_payable_by_jurisdiction(entries)

# DE -> payable 75.00
print(results["DE"].vat_payable)

# FR -> payable 0.00, credit 15.00
print(results["FR"].vat_credit_carry_forward)
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
