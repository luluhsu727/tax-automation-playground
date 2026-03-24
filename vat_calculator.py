"""Utilities for calculating VAT payable by jurisdiction.

This module focuses on a common VAT position:
    VAT to be paid = output VAT (sales) - input VAT (purchases), floored at 0.

When input VAT exceeds output VAT, the remainder is reported as a VAT credit.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")
SALE = "sale"
PURCHASE = "purchase"
VALID_TRANSACTION_TYPES = {SALE, PURCHASE}


class VatComputationError(ValueError):
    """Raised when a transaction has invalid VAT data."""


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert incoming numbers/strings to Decimal safely."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise VatComputationError(f"Invalid decimal value for '{field_name}': {value}") from exc


def _money(amount: Decimal) -> Decimal:
    """Normalize money to two decimal places."""
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    """A single VAT-relevant transaction."""

    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal
    taxable: bool = True

    def vat_amount(self) -> Decimal:
        """Compute VAT amount for the transaction."""
        if not self.taxable:
            return Decimal("0.00")
        return _money(self.net_amount * self.vat_rate)


def transaction_from_mapping(raw: Mapping[str, Any]) -> Transaction:
    """Build a Transaction from a dict-like payload."""
    try:
        jurisdiction = str(raw["jurisdiction"]).strip()
        transaction_type = str(raw["transaction_type"]).strip().lower()
        net_amount = _to_decimal(raw["net_amount"], field_name="net_amount")
        vat_rate = _to_decimal(raw["vat_rate"], field_name="vat_rate")
    except KeyError as exc:
        raise VatComputationError(f"Missing required field: {exc.args[0]}") from exc

    taxable = bool(raw.get("taxable", True))
    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=transaction_type,
        net_amount=net_amount,
        vat_rate=vat_rate,
        taxable=taxable,
    )


def _validate_transaction(transaction: Transaction) -> None:
    if not transaction.jurisdiction:
        raise VatComputationError("Transaction jurisdiction must be a non-empty string.")
    if transaction.transaction_type not in VALID_TRANSACTION_TYPES:
        raise VatComputationError(
            f"Unsupported transaction_type '{transaction.transaction_type}'. "
            f"Expected one of {sorted(VALID_TRANSACTION_TYPES)}."
        )
    if transaction.net_amount < 0:
        raise VatComputationError("Transaction net_amount cannot be negative.")
    if transaction.vat_rate < 0:
        raise VatComputationError("Transaction vat_rate cannot be negative.")


def calculate_vat_position_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, dict[str, Decimal]]:
    """Calculate VAT position for each jurisdiction.

    Returns:
        {
            "<jurisdiction>": {
                "output_vat": Decimal(...),
                "input_vat": Decimal(...),
                "vat_payable": Decimal(...),
                "vat_credit": Decimal(...),
            }
        }
    """

    buckets: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for transaction in transactions:
        _validate_transaction(transaction)
        vat_amount = transaction.vat_amount()
        stats = buckets[transaction.jurisdiction]
        if transaction.transaction_type == SALE:
            stats["output_vat"] += vat_amount
        else:
            stats["input_vat"] += vat_amount

    positions: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _money(buckets[jurisdiction]["output_vat"])
        input_vat = _money(buckets[jurisdiction]["input_vat"])
        net = _money(output_vat - input_vat)
        vat_payable = net if net > 0 else Decimal("0.00")
        vat_credit = -net if net < 0 else Decimal("0.00")
        positions[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _money(vat_payable),
            "vat_credit": _money(vat_credit),
        }

    return positions


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Return only the VAT payable amount for each jurisdiction."""
    positions = calculate_vat_position_by_jurisdiction(transactions)
    return {jurisdiction: values["vat_payable"] for jurisdiction, values in positions.items()}

