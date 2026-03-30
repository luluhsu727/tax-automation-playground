"""Compatibility wrapper exposing VAT payable helpers."""

from jurisdiction_vat_payable import (  # noqa: F401
    compute_vat_payable_by_jurisdiction,
    generate_vat_payable_per_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    load_transactions,
    write_summary,
)

