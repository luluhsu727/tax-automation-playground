from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_rate(rate: Any) -> Decimal:
    normalized = _to_decimal(rate, "vat_rate")
    if normalized < 0:
        raise ValueError("VAT rate cannot be negative")
    if normalized > 1:
        return normalized / Decimal("100")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _extract_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        if vat_amount < 0:
            raise ValueError("vat_amount cannot be negative")
        return vat_amount

    if "amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Transaction must provide either vat_amount, or both amount and vat_rate"
        )

    amount = _to_decimal(transaction["amount"], "amount")
    if amount < 0:
        raise ValueError("amount cannot be negative")

    rate = _normalize_rate(transaction["vat_rate"])
    is_inclusive = bool(transaction.get("is_vat_inclusive", False))

    if is_inclusive:
        # Inclusive formula: VAT = gross - gross / (1 + rate)
        return amount - (amount / (Decimal("1") + rate))

    return amount * rate


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Build a VAT position per jurisdiction.

    Supported transaction formats:
      1) {"jurisdiction": "DE", "output_vat": 100, "input_vat": 20}
      2) {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": 100}
      3) {"jurisdiction": "DE", "transaction_type": "purchase", "amount": 200, "vat_rate": 0.2}

    Transaction types:
      - output VAT: sale, output, revenue
      - input VAT: purchase, input, expense
    """
    aggregated: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for index, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(f"Transaction at index {index} is missing a valid jurisdiction")

        if "output_vat" in transaction or "input_vat" in transaction:
            output = _to_decimal(transaction.get("output_vat", 0), "output_vat")
            input_vat = _to_decimal(transaction.get("input_vat", 0), "input_vat")
            if output < 0 or input_vat < 0:
                raise ValueError("output_vat and input_vat cannot be negative")
            aggregated[jurisdiction]["output_vat"] += output
            aggregated[jurisdiction]["input_vat"] += input_vat
            continue

        tx_type = str(transaction.get("transaction_type", "")).strip().lower()
        vat_amount = _extract_vat_amount(transaction)

        if tx_type in {"sale", "output", "revenue"}:
            aggregated[jurisdiction]["output_vat"] += vat_amount
        elif tx_type in {"purchase", "input", "expense"}:
            aggregated[jurisdiction]["input_vat"] += vat_amount
        else:
            raise ValueError(
                f"Transaction at index {index} has unsupported transaction_type: {tx_type!r}"
            )

    report: Dict[str, Dict[str, float]] = {}
    for jurisdiction in sorted(aggregated):
        output_vat = _quantize(aggregated[jurisdiction]["output_vat"])
        input_vat = _quantize(aggregated[jurisdiction]["input_vat"])
        payable = _quantize(output_vat - input_vat)

        if payable > 0:
            position = "payable"
        elif payable < 0:
            position = "refund"
        else:
            position = "settled"

        report[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(payable),
            "position": position,
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction from JSON transactions."
    )
    parser.add_argument(
        "input_file",
        help="Path to a JSON file containing a list of transactions.",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as file:
        transactions = json.load(file)

    if not isinstance(transactions, list):
        raise ValueError("Input JSON must be a list of transactions")

    report = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
