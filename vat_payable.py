"""Backward-compatible exports for VAT payable calculations."""

from jurisdiction_vat_payable import (  # noqa: F401
    DEFAULT_VAT_RATES,
    calculate_vat_payable_by_jurisdiction,
    compute_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    load_transactions,
    main,
    parse_args,
    write_summary,
)
