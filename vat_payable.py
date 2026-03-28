"""VAT payable calculation utilities.

This module calculates VAT payable per jurisdiction using transaction data.
VAT payable is computed as:

    output VAT (sales) - input VAT (purchases)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Literal, Mapping, MutableMapping, Optional


TransactionType = Literal["sale", "purchase"]


@dataclass(frozen=True)
class Transaction:
    """Represents one VAT-relevant transaction."""

    jurisdiction: str
    transaction_type: TransactionType
    amount: Decimal
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert a numeric input to Decimal safely."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion branch
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_transaction(raw_transaction: Mapping[str, Any]) -> Transaction:
    """Parse and validate a transaction mapping."""
    jurisdiction = str(raw_transaction.get("jurisdiction", "")).strip()
    if not jurisdiction:
        raise ValueError("Each transaction must include a non-empty 'jurisdiction'.")

    transaction_type_raw = str(raw_transaction.get("transaction_type", "")).strip().lower()
    if transaction_type_raw not in {"sale", "purchase"}:
        raise ValueError(
            "Each transaction must include 'transaction_type' with value 'sale' or 'purchase'."
        )
    transaction_type: TransactionType = transaction_type_raw  # type: ignore[assignment]

    amount = _to_decimal(raw_transaction.get("amount", 0), "amount")

    vat_amount_raw = raw_transaction.get("vat_amount")
    vat_rate_raw = raw_transaction.get("vat_rate")
    vat_amount = _to_decimal(vat_amount_raw, "vat_amount") if vat_amount_raw is not None else None
    vat_rate = _to_decimal(vat_rate_raw, "vat_rate") if vat_rate_raw is not None else None

    if vat_amount is None and vat_rate is None:
        raise ValueError("Each transaction must include either 'vat_amount' or 'vat_rate'.")

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=transaction_type,
        amount=amount,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
    )


def _resolve_vat_amount(transaction: Transaction) -> Decimal:
    """Resolve VAT amount from explicit VAT or amount * rate."""
    if transaction.vat_amount is not None:
        return transaction.vat_amount
    assert transaction.vat_rate is not None  # guaranteed by validation
    return transaction.amount * transaction.vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    precision: str = "0.01",
) -> Dict[str, float]:
    """Calculate VAT payable for each jurisdiction.

    Args:
        transactions: iterable of dictionaries with keys:
            - jurisdiction (str)
            - transaction_type ("sale" | "purchase")
            - amount (number)
            - vat_rate (number, optional if vat_amount is provided)
            - vat_amount (number, optional if vat_rate is provided)
        precision: decimal precision as quantize step, defaults to cents (0.01).

    Returns:
        A dictionary mapping jurisdiction to VAT payable amount as float.
        Positive means payable; negative means refundable.
    """

    output_vat_by_jurisdiction: MutableMapping[str, Decimal] = defaultdict(lambda: Decimal("0"))
    input_vat_by_jurisdiction: MutableMapping[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for raw_transaction in transactions:
        transaction = _normalize_transaction(raw_transaction)
        vat_amount = _resolve_vat_amount(transaction)

        if transaction.transaction_type == "sale":
            output_vat_by_jurisdiction[transaction.jurisdiction] += vat_amount
        else:
            input_vat_by_jurisdiction[transaction.jurisdiction] += vat_amount

    quantize_step = _to_decimal(precision, "precision")
    jurisdictions = set(output_vat_by_jurisdiction) | set(input_vat_by_jurisdiction)
    result: Dict[str, float] = {}
    for jurisdiction in sorted(jurisdictions):
        payable = output_vat_by_jurisdiction[jurisdiction] - input_vat_by_jurisdiction[jurisdiction]
        payable = payable.quantize(quantize_step, rounding=ROUND_HALF_UP)
        result[jurisdiction] = float(payable)

    return result


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, float]:
    """Compatibility alias for the core VAT payable calculation."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def build_report(
    transactions: Iterable[Mapping[str, Any]],
    *,
    precision: str = "0.01",
) -> Dict[str, Dict[str, float]]:
    """Build report object with VAT payable by jurisdiction."""
    return {
        "vat_payable_by_jurisdiction": calculate_vat_payable_by_jurisdiction(
            transactions,
            precision=precision,
        )
    }


def _main() -> int:
    """CLI entrypoint.

    Usage:
        python vat_payable.py input.json
    """
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python vat_payable.py <input-json-path>")
        return 1

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    transactions: List[Dict[str, Any]] = payload.get("transactions", [])
    report = build_report(transactions)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
