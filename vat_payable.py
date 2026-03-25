from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Any


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    net_amount: Decimal
    vat_rate: Decimal
    transaction_type: str = "sale"
    vat_amount: Decimal | None = None


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"Invalid decimal value for {field_name}: {value}") from exc


def _normalize_transaction(entry: Mapping[str, Any] | Transaction) -> Transaction:
    if isinstance(entry, Transaction):
        tx = entry
    else:
        tx = Transaction(
            jurisdiction=str(entry.get("jurisdiction", "")).strip(),
            net_amount=_to_decimal(entry.get("net_amount", "0"), "net_amount"),
            vat_rate=_to_decimal(entry.get("vat_rate", "0"), "vat_rate"),
            transaction_type=str(entry.get("transaction_type", "sale")).strip().lower(),
            vat_amount=(
                None
                if entry.get("vat_amount") is None
                else _to_decimal(entry.get("vat_amount"), "vat_amount")
            ),
        )

    if not tx.jurisdiction:
        raise ValueError("Transaction jurisdiction is required")
    if tx.net_amount < 0:
        raise ValueError("net_amount must be non-negative")
    if tx.vat_rate < 0:
        raise ValueError("vat_rate must be non-negative")
    if tx.transaction_type not in {"sale", "purchase"}:
        raise ValueError("transaction_type must be 'sale' or 'purchase'")

    return tx


def generate_vat_payable_per_jurisdiction(
    transactions: Iterable[Mapping[str, Any] | Transaction],
) -> dict[str, Decimal]:
    """Return net VAT payable for each jurisdiction.

    VAT for sales increases the payable amount.
    VAT for purchases decreases the payable amount.
    """
    payable_by_jurisdiction: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for raw_tx in transactions:
        tx = _normalize_transaction(raw_tx)
        vat_component = (
            tx.vat_amount if tx.vat_amount is not None else tx.net_amount * tx.vat_rate
        )
        sign = Decimal("1") if tx.transaction_type == "sale" else Decimal("-1")
        payable_by_jurisdiction[tx.jurisdiction] += sign * vat_component

    rounded = {
        jurisdiction: amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in payable_by_jurisdiction.items()
    }
    return dict(sorted(rounded.items(), key=lambda item: item[0]))
