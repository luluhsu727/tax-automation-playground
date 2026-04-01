"""Generate VAT payable totals by jurisdiction."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWO_DECIMALS = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    # Support both decimal rates (0.2) and percentage rates (20).
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _calculate_transaction_vat(transaction: Mapping[str, Any], index: int) -> Decimal:
    vat_amount = transaction.get("vat_amount")
    if vat_amount is not None:
        amount = _to_decimal(vat_amount, "vat_amount")
    else:
        if "taxable_amount" not in transaction:
            raise ValueError(
                f"Transaction at index {index} must include vat_amount or taxable_amount"
            )
        if "vat_rate" not in transaction:
            raise ValueError(
                f"Transaction at index {index} must include vat_rate when vat_amount is not set"
            )
        taxable_amount = _to_decimal(transaction["taxable_amount"], "taxable_amount")
        vat_rate = _normalize_rate(_to_decimal(transaction["vat_rate"], "vat_rate"))
        amount = taxable_amount * vat_rate

    return amount.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, str]:
    """Aggregate VAT payable totals by jurisdiction.

    Each transaction must include:
    - jurisdiction: string
    and either:
    - vat_amount
    or:
    - taxable_amount and vat_rate
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)

    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, Mapping):
            raise ValueError(f"Transaction at index {index} must be an object")
        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(
                f"Transaction at index {index} has invalid jurisdiction: {jurisdiction!r}"
            )

        normalized_jurisdiction = jurisdiction.strip()
        totals[normalized_jurisdiction] += _calculate_transaction_vat(transaction, index)

    return {
        jurisdiction: str(total.quantize(TWO_DECIMALS, rounding=ROUND_HALF_UP))
        for jurisdiction, total in sorted(totals.items())
    }


def _load_transactions(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping) and isinstance(payload.get("transactions"), list):
        return payload["transactions"]
    raise ValueError("Input must be a JSON array or an object with a 'transactions' array")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="-",
        help="Path to input JSON file. Use '-' or omit for stdin.",
    )
    args = parser.parse_args(argv)

    try:
        if args.input_file == "-":
            raw_data = sys.stdin.read()
        else:
            raw_data = Path(args.input_file).read_text(encoding="utf-8")
        payload = json.loads(raw_data)
        transactions = _load_transactions(payload)
        result = generate_vat_payable_by_jurisdiction(transactions)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
