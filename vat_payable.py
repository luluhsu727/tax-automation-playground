"""VAT payable calculator grouped by jurisdiction.

The main entry point is ``calculate_vat_payable_by_jurisdiction``.
It accepts a list/iterable of transaction mappings and returns a mapping
``{jurisdiction: vat_payable}``.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import sys
from typing import Any, Dict, Iterable, Mapping

_OUTPUT_TYPES = {
    "sale",
    "sales",
    "output",
    "collected",
    "invoice_out",
    "outgoing",
    "customer_invoice",
}
_INPUT_TYPES = {
    "purchase",
    "purchases",
    "expense",
    "input",
    "paid",
    "invoice_in",
    "incoming",
    "vendor_bill",
}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"Missing required numeric field: {field_name}")

    if isinstance(value, bool):
        raise ValueError(f"Invalid numeric value for {field_name}: {value!r}")

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field_name}: {value!r}") from exc


def _normalize_rate(rate: Any) -> Decimal:
    rate_decimal = _to_decimal(rate, "vat_rate")
    if rate_decimal < 0:
        raise ValueError("vat_rate cannot be negative")
    # Supports rates expressed as either 0.2 or 20.
    if rate_decimal > 1:
        rate_decimal = rate_decimal / Decimal("100")
    return rate_decimal


def _extract_jurisdiction(transaction: Mapping[str, Any]) -> str:
    jurisdiction = (
        transaction.get("jurisdiction")
        or transaction.get("country")
        or transaction.get("region")
    )
    if jurisdiction is None or str(jurisdiction).strip() == "":
        raise ValueError("Each transaction must include a jurisdiction/country/region")
    return str(jurisdiction)


def _transaction_direction(transaction: Mapping[str, Any]) -> Decimal:
    marker = (
        transaction.get("transaction_type")
        or transaction.get("type")
        or transaction.get("direction")
        or transaction.get("kind")
    )
    if marker is None:
        return Decimal("1")

    normalized = str(marker).strip().lower()
    if normalized in _INPUT_TYPES:
        return Decimal("-1")
    if normalized in _OUTPUT_TYPES:
        return Decimal("1")
    # Unknown markers default to output VAT.
    return Decimal("1")


def _extract_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction.get("vat_amount") is not None:
        return _to_decimal(transaction.get("vat_amount"), "vat_amount")

    amount = None
    for amount_key in ("amount", "net_amount", "taxable_amount", "base_amount"):
        if amount_key in transaction and transaction.get(amount_key) is not None:
            amount = _to_decimal(transaction.get(amount_key), amount_key)
            break

    if amount is None:
        raise ValueError(
            "Each transaction must include vat_amount or one of "
            "amount/net_amount/taxable_amount/base_amount"
        )

    if "vat_rate" not in transaction or transaction.get("vat_rate") is None:
        raise ValueError("Missing vat_rate when vat_amount is not provided")

    rate = _normalize_rate(transaction.get("vat_rate"))
    return amount * rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    rounding: int = 2,
    include_zero: bool = False,
) -> Dict[str, float]:
    """Compute VAT payable totals grouped by jurisdiction.

    Rules:
    - output VAT (sales) increases payable balance
    - input VAT (purchases/expenses) decreases payable balance
    - VAT can be supplied directly via ``vat_amount``
    - or computed via ``amount`` + ``vat_rate`` (``vat_rate`` supports 0.2 or 20)
    """

    if rounding < 0:
        raise ValueError("rounding must be >= 0")

    totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            raise TypeError("Each transaction must be a mapping/dictionary")

        jurisdiction = _extract_jurisdiction(transaction)
        direction = _transaction_direction(transaction)
        vat_amount = _extract_vat_amount(transaction)
        totals[jurisdiction] += vat_amount * direction

    quantum = Decimal("1").scaleb(-rounding)
    result: Dict[str, float] = {}
    for jurisdiction in sorted(totals):
        total = totals[jurisdiction].quantize(quantum, rounding=ROUND_HALF_UP)
        if include_zero or total != 0:
            result[jurisdiction] = float(total)
    return result


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    rounding: int = 2,
    include_zero: bool = False,
) -> Dict[str, float]:
    """Alias for calculate_vat_payable_by_jurisdiction."""

    return calculate_vat_payable_by_jurisdiction(
        transactions, rounding=rounding, include_zero=include_zero
    )


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    *,
    rounding: int = 2,
    include_zero: bool = False,
) -> Dict[str, float]:
    """Compatibility alias matching the goal phrasing."""

    return calculate_vat_payable_by_jurisdiction(
        transactions, rounding=rounding, include_zero=include_zero
    )


def _transactions_from_payload(payload: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("transactions"), list):
        return payload["transactions"]
    raise ValueError("Input JSON must be a list or an object with 'transactions' list")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) > 1:
        print("Usage: python vat_payable.py [input.json]", file=sys.stderr)
        return 2

    try:
        if argv:
            with open(argv[0], "r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            payload = json.load(sys.stdin)

        transactions = _transactions_from_payload(payload)
        result = calculate_vat_payable_by_jurisdiction(transactions)
    except Exception as exc:  # pragma: no cover - CLI safety net.
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
