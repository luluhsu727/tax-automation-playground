"""Backward-compatible VAT module wrapper.

Some task variants import from `vat` rather than `vat_payable`.
"""

from vat_payable import Transaction, generate_vat_payable_by_jurisdiction

__all__ = ["Transaction", "generate_vat_payable_by_jurisdiction"]
