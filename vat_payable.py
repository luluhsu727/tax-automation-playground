"""Generate VAT to be paid for each jurisdiction.

The core function is:
    calculate_vat_payable_by_jurisdiction(transactions)

It accepts either dictionaries or Transaction objects and returns a mapping:
    { "<jurisdiction>": Decimal("<amount>"), ... }
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping

MONEY_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction.

    transaction_type can be one of:
    - sale/output/output_vat
    - purchase/input/input_vat/expense
    """

    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _to_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _normalize_transaction_type(transaction_type: str) -> str:
    normalized = transaction_type.strip().lower()
    if normalized in {"sale", "sales", "output", "output_vat"}:
        return "sale"
    if normalized in {"purchase", "purchases", "input", "input_vat", "expense"}:
        return "purchase"
    raise ValueError(
        "Unsupported transaction type. Expected sale/output or purchase/input aliases."
    )


def _parse_vat_rate(raw_rate: object) -> Decimal:
    if isinstance(raw_rate, str) and raw_rate.strip().endswith("%"):
        parsed = _to_decimal(raw_rate.strip()[:-1], "vat_rate")
        return parsed / Decimal("100")
    parsed = _to_decimal(raw_rate, "vat_rate")
    if parsed > 1:
        return parsed / Decimal("100")
    return parsed


def _vat_from_record(record: Mapping[str, object]) -> Decimal:
    if "vat_amount" in record and record.get("vat_amount") is not None:
        vat_amount = _to_decimal(record.get("vat_amount"), "vat_amount")
        return _to_money(vat_amount)

    amount_value = record.get("net_amount", record.get("amount"))
    rate_value = record.get("vat_rate")
    if amount_value is None or rate_value is None:
        raise ValueError(
            "Record must contain either 'vat_amount' or both "
            "'amount/net_amount' and 'vat_rate'."
        )

    amount = _to_decimal(amount_value, "amount")
    rate = _parse_vat_rate(rate_value)
    return _to_money(amount * rate)


def transaction_from_record(record: Mapping[str, object]) -> Transaction:
    """Create a Transaction from a dictionary-like record."""

    jurisdiction = str(record.get("jurisdiction", "")).strip()
    if not jurisdiction:
        raise ValueError("Record is missing a non-empty 'jurisdiction'")

    raw_type = record.get("transaction_type", record.get("type"))
    if raw_type is None:
        raise ValueError("Record is missing 'transaction_type' (or alias 'type')")

    transaction_type = _normalize_transaction_type(str(raw_type))
    vat_amount = _vat_from_record(record)
    if vat_amount < 0:
        raise ValueError("VAT amount cannot be negative")

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=transaction_type,
        vat_amount=vat_amount,
    )


def load_transactions(path: str | Path) -> list[Transaction]:
    file_path = Path(path)
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("transactions"), list):
        records = payload["transactions"]
    else:
        raise ValueError(
            "Input JSON must be a transaction list or an object with a 'transactions' list"
        )

    return [transaction_from_record(record) for record in records]


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Return net VAT payable per jurisdiction.

    Net VAT payable = VAT from sales - VAT from purchases
    """

    totals: dict[str, Decimal] = {}
    for raw_transaction in transactions:
        transaction = (
            raw_transaction
            if isinstance(raw_transaction, Transaction)
            else transaction_from_record(raw_transaction)
        )
        current_total = totals.get(transaction.jurisdiction, Decimal("0"))
        if transaction.transaction_type == "sale":
            current_total += transaction.vat_amount
        elif transaction.transaction_type == "purchase":
            current_total -= transaction.vat_amount
        totals[transaction.jurisdiction] = current_total

    finalized: dict[str, Decimal] = {}
    for jurisdiction, total in totals.items():
        if floor_at_zero and total < 0:
            total = Decimal("0")
        finalized[jurisdiction] = _to_money(total)
    return finalized


def _format_report(vat_by_jurisdiction: dict[str, Decimal]) -> str:
    if not vat_by_jurisdiction:
        return "No transactions."
    lines = []
    for jurisdiction in sorted(vat_by_jurisdiction):
        lines.append(f"{jurisdiction}: {vat_by_jurisdiction[jurisdiction]:.2f}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to JSON transactions file")
    parser.add_argument(
        "--floor-at-zero",
        action="store_true",
        help="Set negative VAT payable amounts to 0.00",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON mapping jurisdiction to 2dp string amount",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.input_file)
    vat_by_jurisdiction = calculate_vat_payable_by_jurisdiction(
        transactions,
        floor_at_zero=args.floor_at_zero,
    )

    if args.json:
        payload = {key: f"{value:.2f}" for key, value in sorted(vat_by_jurisdiction.items())}
        print(json.dumps(payload, indent=2))
    else:
        print(_format_report(vat_by_jurisdiction))


if __name__ == "__main__":
    main()
