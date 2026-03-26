"""Compatibility facade for VAT payable calculations.

Different automation runs in this repository import from different module names.
This module re-exports the stable APIs used by VAT calculation tests.
"""

from vat_payable import (
    PURCHASE,
    SALE,
    Transaction,
    VALID_TRANSACTION_TYPES,
    VatComputationError,
    calculate_vat_position_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    transaction_from_mapping,
)

__all__ = [
    "PURCHASE",
    "SALE",
    "Transaction",
    "VALID_TRANSACTION_TYPES",
    "VatComputationError",
    "calculate_vat_position_by_jurisdiction",
    "generate_vat_to_be_paid_by_jurisdiction",
    "transaction_from_mapping",
]
