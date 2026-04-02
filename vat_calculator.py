from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")
SALE_TYPES = {"sale", "output", "collected"}
PURCHASE_TYPES = {"purchase", "input", "paid"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_rate(raw_rate: Decimal) -> Decimal:
    if raw_rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if raw_rate > 1:
        return raw_rate / Decimal("100")
    return raw_rate


def _resolve_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    vat_amount = transaction.get("vat_amount")
    if vat_amount is not None:
        vat = _to_decimal(vat_amount, "vat_amount")
        if vat < 0:
            raise ValueError("vat_amount cannot be negative")
        return vat

    if "amount" not in transaction:
        raise ValueError("Transaction is missing required field: amount")
    if "vat_rate" not in transaction:
        raise ValueError("Transaction is missing required field: vat_rate")

    amount = _to_decimal(transaction["amount"], "amount")
    rate = _normalize_rate(_to_decimal(transaction["vat_rate"], "vat_rate"))

    if amount < 0:
        raise ValueError("amount cannot be negative")

    return (amount * rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_to_be_paid(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for idx, transaction in enumerate(transactions, start=1):
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Transaction #{idx} is missing required field: jurisdiction")

        tx_type = str(transaction.get("transaction_type", "")).strip().lower()
        if tx_type in SALE_TYPES:
            sign = Decimal("1")
        elif tx_type in PURCHASE_TYPES:
            sign = Decimal("-1")
        else:
            raise ValueError(
                f"Transaction #{idx} has unknown transaction_type: {transaction.get('transaction_type')!r}"
            )

        vat = _resolve_vat_amount(transaction)
        totals[jurisdiction] += sign * vat

    # Standard currency rounding for final payable amount.
    return {
        jurisdiction: amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in sorted(totals.items())
    }


def _serialize(totals: Mapping[str, Decimal]) -> dict[str, str]:
    return {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in totals.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid per jurisdiction from a JSON transaction file."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to a JSON file containing an array of transactions.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON output. Defaults to stdout.",
    )
    args = parser.parse_args()

    raw = args.input_file.read_text(encoding="utf-8")
    transactions = json.loads(raw)
    if not isinstance(transactions, list):
        raise ValueError("Input JSON must be an array of transactions")

    totals = generate_vat_to_be_paid(transactions)
    payload = json.dumps(_serialize(totals), indent=2, sort_keys=True)

    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
        return
    print(payload)


if __name__ == "__main__":
    main()
