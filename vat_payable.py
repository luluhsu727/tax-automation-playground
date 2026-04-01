"""Utilities to compute VAT payable per jurisdiction."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0.00")
SALE_TYPES = {"sale", "sales", "output"}
PURCHASE_TYPES = {"purchase", "purchases", "input"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for '{field_name}': {value!r}") from exc


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_jurisdiction(value: Any, index: int) -> str:
    if value is None:
        raise ValueError(f"Missing jurisdiction for transaction at index {index}")

    jurisdiction = str(value).strip()
    if not jurisdiction:
        raise ValueError(f"Empty jurisdiction for transaction at index {index}")

    return jurisdiction.upper()


def _extract_vat_amount(transaction: Mapping[str, Any], index: int) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return _round_money(_to_decimal(transaction["vat_amount"], "vat_amount"))

    if "net_amount" not in transaction:
        raise ValueError(f"Missing net_amount for transaction at index {index}")
    if "vat_rate" not in transaction:
        raise ValueError(f"Missing vat_rate for transaction at index {index}")

    net_amount = _to_decimal(transaction["net_amount"], "net_amount")
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
    return _round_money(net_amount * vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Generate VAT summary per jurisdiction.

    Each transaction must include:
      - jurisdiction (str)
      - type: sale/sales/output or purchase/purchases/input
      - either vat_amount, or net_amount + vat_rate
    """

    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": ZERO, "input_vat": ZERO}
    )

    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, Mapping):
            raise ValueError(f"Transaction at index {index} must be an object")

        jurisdiction = _normalize_jurisdiction(transaction.get("jurisdiction"), index)
        tx_type = str(transaction.get("type", "")).strip().lower()

        if tx_type in SALE_TYPES:
            bucket = "output_vat"
        elif tx_type in PURCHASE_TYPES:
            bucket = "input_vat"
        else:
            raise ValueError(
                f"Unsupported transaction type at index {index}: {transaction.get('type')!r}"
            )

        vat_amount = _extract_vat_amount(transaction, index)
        totals[jurisdiction][bucket] += vat_amount

    summary: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _round_money(totals[jurisdiction]["output_vat"])
        input_vat = _round_money(totals[jurisdiction]["input_vat"])
        net_vat = _round_money(output_vat - input_vat)
        vat_payable = net_vat if net_vat > ZERO else ZERO
        vat_refundable = -net_vat if net_vat < ZERO else ZERO

        summary[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": vat_payable,
            "vat_refundable": vat_refundable,
        }

    return summary


def format_summary_for_json(
    summary: Mapping[str, Mapping[str, Decimal]]
) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {
            key: f"{_round_money(value):.2f}" for key, value in values.items()
        }
        for jurisdiction, values in summary.items()
    }


def load_transactions_from_json(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("transactions"), list):
        return payload["transactions"]

    raise ValueError(
        "Input JSON must be either a list of transactions or an object with a "
        "'transactions' list."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction from transaction data."
    )
    parser.add_argument("input", help="Path to JSON file with transactions")
    parser.add_argument(
        "-o", "--output", help="Optional output file path for the VAT summary JSON"
    )
    args = parser.parse_args()

    transactions = load_transactions_from_json(args.input)
    summary = generate_vat_payable_by_jurisdiction(transactions)
    json_payload = json.dumps(format_summary_for_json(summary), indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(json_payload + "\n")
    else:
        print(json_payload)


if __name__ == "__main__":
    main()
