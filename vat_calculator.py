"""High-level VAT calculator API.

This module keeps backwards-compatible names used by earlier iterations
of the challenge while generating VAT to be paid for each jurisdiction.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Mapping

from vat_core import VatError, money, normalize_jurisdiction, to_decimal, to_rate

TWOPLACES = Decimal("0.01")
SALE = "sale"
PURCHASE = "purchase"
VALID_TRANSACTION_TYPES = {SALE, PURCHASE}


class VatComputationError(VatError):
    """Raised when a transaction has invalid VAT data."""


@dataclass(frozen=True)
class Transaction:
    """A single VAT-relevant transaction."""

    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal
    taxable: bool = True

    def vat_amount(self) -> Decimal:
        if not self.taxable:
            return Decimal("0.00")
        return money(self.net_amount * self.vat_rate)


def transaction_from_mapping(raw: Mapping[str, Any]) -> Transaction:
    """Build a Transaction from a dict-like payload."""
    try:
        jurisdiction = normalize_jurisdiction(raw["jurisdiction"])
        transaction_type = str(raw["transaction_type"]).strip().lower()
        net_amount = to_decimal(raw["net_amount"], field_name="net_amount")
        vat_rate = to_rate(raw["vat_rate"], field_name="vat_rate")
    except KeyError as exc:
        raise VatComputationError(f"Missing required field: {exc.args[0]}") from exc
    except VatError as exc:
        raise VatComputationError(str(exc)) from exc

    if transaction_type not in VALID_TRANSACTION_TYPES:
        raise VatComputationError(
            f"Unsupported transaction_type '{transaction_type}'. "
            f"Expected one of {sorted(VALID_TRANSACTION_TYPES)}."
        )

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
        raise VatComputationError("Transaction jurisdiction must be non-empty.")
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
    """Calculate output/input VAT and derive payable/credit by jurisdiction."""
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
        output_vat = money(buckets[jurisdiction]["output_vat"])
        input_vat = money(buckets[jurisdiction]["input_vat"])
        net = money(output_vat - input_vat)
        vat_payable = net if net > 0 else Decimal("0.00")
        vat_credit = -net if net < 0 else Decimal("0.00")
        positions[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": money(vat_payable),
            "vat_credit": money(vat_credit),
        }

    return positions


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Return only VAT payable values, floored at 0 by jurisdiction."""
    positions = calculate_vat_position_by_jurisdiction(transactions)
    return {jurisdiction: values["vat_payable"] for jurisdiction, values in positions.items()}


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, Decimal]:
    """Compatibility alias for challenge wording."""
    return generate_vat_to_be_paid_by_jurisdiction(transactions)
